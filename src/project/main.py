import threading
import time
import importlib
import os
import asyncio
from datetime import datetime
from webex_bot.webex_bot import WebexBot
from webex_bot.models.command import Command

# Your custom API and Utility imports
from apis.jira_client import fetch_all_mule_issues_with_token, compare_issue_lists
from apis.webex_client import IterateThroughListOfMules
from utils.logger import setup_logger
import utils.seed_issues

# --- CONFIGURATION ---
USE_SEED_DATA = False  # Set to False for production JIRA API

logger = setup_logger(__name__)

# --- SHARED STATE & THREAD SAFETY ---
# data_lock ensures that the background thread and bot commands don't 
# access the shared dictionary at the exact same microsecond.
data_lock = threading.Lock()

monitor_stats = {
    "status": "Initializing...",
    "last_run": "Never",
    "issue_count": 0,
    "last_change_detected": "None",
    "last_changes_list": [],
    "full_issue_list": []  # The master list used for searching
}

# --- BOT COMMANDS ---

class StatusCommand(Command):
    def __init__(self):
        super().__init__(
            command_keyword="status",
            help_message="Check the current status of the JIRA monitor.",
            card=None
        )

    def execute(self, message, attachment_actions, activity):
        with data_lock:
            mode = "SEED DATA" if USE_SEED_DATA else "REAL JIRA API"
            status = monitor_stats.get("status")
            count = monitor_stats.get("issue_count")
            last_run = monitor_stats.get("last_run")
            
        return (f"🤖 **JIRA Monitor Status:** {status}\n"
                f"- **Mode:** `{mode}`\n"
                f"- **Issues Tracked:** {count}\n"
                f"- **Last Check:** {last_run}")

class LatestChangesCommand(Command):
    def __init__(self):
        super().__init__(
            command_keyword="latest",
            help_message="Show the 10 most recent JIRA changes detected.",
            card=None
        )

    def execute(self, message, attachment_actions, activity):
        with data_lock:
            changes = monitor_stats.get("last_changes_list", [])
            last_time = monitor_stats.get("last_change_detected", "None")
        
        if not changes:
            return "No changes detected since the bot started."

        response = f"🔍 **Latest Changes Detected ({last_time}):**\n\n"
        for issue in changes[:10]:
            jira_num = issue.get('JiraNumber', 'N/A')
            case_num = issue.get('CaseNumber', 'N/A')
            mule_id = issue.get('MuleLink', '')
            
            # Construct URLs
            jira_url = f"https://meraki.atlassian.net/browse/{jira_num}"
            sf_url = f"https://meraki.my.salesforce.com/{mule_id}"
            
            response += (f"🔹 **[{jira_num}]({jira_url})**: {issue.get('JiraTitle')}\n"
                         f"   - 🔗 Salesforce: [{case_num}]({sf_url})\n\n")
        return response

class SearchIssuesCommand(Command):
    def __init__(self):
        super().__init__(
            command_keyword="search",
            help_message="Search issues. type 'search' for details",
            card=None
        )

    def execute(self, message, attachment_actions, activity):
        query = message.strip().lower()
        
        # 1. Provide a Guide if no keywords are provided
        if not query:
            return (
                "📖 **How to use Smart Search:**\n\n"
                "Type `search` followed by your keywords:\n"
                "1. **Multiple Keywords**: Finds issues containing *all* words.\n"
                "   - Example: `search client vpn` \n"
                "2. **Exclusion**: Use a minus sign `-` to hide certain results.\n"
                "   - Example: `search snapshot -closed` (Hides closed issues)\n"
                "3. **Specific IDs**: Search by Jira ID or Salesforce Case Number.\n"
            )

        # 2. Parse query into positive and negative terms
        all_terms = query.split()
        pos_terms = [t for t in all_terms if not t.startswith('-')]
        neg_terms = [t[1:] for t in all_terms if t.startswith('-') and len(t) > 1]
        
        with data_lock:
            full_list = monitor_stats.get("full_issue_list", [])
            scored_matches = []

            for issue in full_list:
                # Extract fields for searching
                j_num = str(issue.get('JiraNumber', '')).lower()
                title = str(issue.get('JiraTitle', '')).lower()
                status = str(issue.get('JiraStatus', '')).lower()
                sev = str(issue.get('Severity', '')).lower()
                case = str(issue.get('CaseNumber', '')).lower()
                
                # Combine fields into one searchable string
                combined_text = f"{j_num} {title} {status} {sev} {case}"

                # Exclusion Logic: If any negative term is found, skip this issue
                if any(term in combined_text for term in neg_terms):
                    continue

                # Inclusion Logic: Check if ALL positive terms are present
                if all(term in combined_text for term in pos_terms):
                    # Calculate relevance score for sorting
                    score = 0
                    for term in pos_terms:
                        if term in j_num: score += 10 # ID matches are top priority
                        if term in title: score += 5  # Title matches are high priority
                        if term in case:  score += 3  # Case number matches
                    
                    scored_matches.append((score, issue))

        if not scored_matches:
            return f"No issues found matching all terms: `{query}`"

        # 3. Sort by score (highest relevance first)
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        final_matches = [item[1] for item in scored_matches]

        response = f"🔎 **Search Results for '{query}':**\n\n"
        for issue in final_matches[:10]:
            jira_num = issue.get('JiraNumber', 'N/A')
            case_num = issue.get('CaseNumber', 'N/A')
            mule_id = issue.get('MuleLink', '')
            
            # Construct URLs
            jira_url = f"https://meraki.atlassian.net/browse/{jira_num}"
            sf_url = f"https://meraki.my.salesforce.com/{mule_id}"
            
            response += (f"🔹 **[{jira_num}]({jira_url})**: {issue.get('JiraTitle')}\n"
                         f"   - Status: `{issue.get('JiraStatus', 'Unknown')}` | Severity: `{issue.get('Severity', 'N/A')}`\n"
                         f"   - 🔗 Salesforce: [{case_num}]({sf_url})\n\n")
        
        if len(final_matches) > 10:
            response += f"⚠️ _Showing first 10 results. Please refine your search for more specific results._"
            
        return response


# --- BACKGROUND MONITORING LOOP ---

def jira_monitor_loop():
    global monitor_stats
    logger.info(f"Starting background JIRA monitoring loop (Seed Mode: {USE_SEED_DATA})...")
    
    try:
        old_list = get_issues()
        with data_lock:
            monitor_stats["full_issue_list"] = old_list
            monitor_stats["issue_count"] = len(old_list)
            monitor_stats["status"] = "Healthy"
        
        while True:
            try:
                time.sleep(60)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                new_list = get_issues()
                changes = compare_issue_lists(old_list, new_list)
                
                with data_lock:
                    monitor_stats["last_run"] = timestamp
                    
                    if changes:
                        monitor_stats["last_change_detected"] = timestamp
                        monitor_stats["last_changes_list"] = changes 
                        logger.info(f"Detected {len(changes)} changes.")
                        IterateThroughListOfMules(changes)
                    
                    # Update master list only if it passes basic validation
                    if len(new_list) >= 10: 
                        old_list = new_list
                        monitor_stats["full_issue_list"] = old_list
                        monitor_stats["issue_count"] = len(new_list)
                        monitor_stats["status"] = "Healthy"
            
            except Exception as e:
                with data_lock:
                    monitor_stats["status"] = f"Error: {str(e)}"
                logger.error(f"Loop error: {e}")
                
    except Exception as e:
        with data_lock:
            monitor_stats["status"] = "CRITICAL: Thread Stopped"
        logger.critical(f"Monitor Thread stopped: {e}")

def get_issues():
    if USE_SEED_DATA:
        importlib.reload(utils.seed_issues)
        return utils.seed_issues.seed_data
    else:
        return fetch_all_mule_issues_with_token()


# --- MAIN EXECUTION ---

if __name__ == "__main__":
    try:
        # Asyncio fix for Python 3.14
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        api_token = os.environ.get("WEBEX_BOT_KEY")
        if not api_token:
            raise KeyError("WEBEX_BOT_KEY not found in environment.")

        bot = WebexBot(teams_bot_token=api_token)

        # Register Commands
        bot.add_command(StatusCommand())
        bot.add_command(LatestChangesCommand())
        bot.add_command(SearchIssuesCommand())

        # Start background thread
        monitor_thread = threading.Thread(target=jira_monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("JIRA Monitor thread started.")

        # Start Bot
        logger.info("Webex Bot is starting...")
        bot.run()

    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)