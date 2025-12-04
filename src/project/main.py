from apis.jira_client import fetch_all_mule_issues_with_token, compare_issue_lists
from apis.webex_client import IterateThroughListOfMules
import time
from utils.logger import setup_logger

# from services.jira_service import get_jira_issue, pretty_print_json, human_readable_issue_summary
# response_data=get_jira_issue('SM-7789')
# human_readable_issue_summary(response_data)

logger = setup_logger(__name__)

def is_list_complete(new_list, old_list, min_expected=100, completeness_ratio=0.8):
    # Check minimum expected number of issues
    if len(new_list) < min_expected:
        return False
    
    
    # Check size ratio compared to old_list
    if old_list and len(new_list) < len(old_list) * completeness_ratio:
        return False
    
    return True

def main():
    logger.info("Starting continuous issue monitoring loop...")
    
    try:
        old_list = fetch_all_mule_issues_with_token()
        logger.info(f"Initial fetch complete. Retrieved {len(old_list)} issues.")
        logger.info(old_list)
        
        while True:
            try:
                logger.info("Waiting...")
                time.sleep(60)  # Wait 1 minute
                
                new_list = fetch_all_mule_issues_with_token()
                logger.info(f"New fetch complete. Retrieved {len(new_list)} issues.")
                
                logger.info("Comparing old and new issue lists for changes...")
                changes = compare_issue_lists(old_list, new_list)
                
                if changes:
                    logger.info(f"Detected {len(changes)} new or changed issues:")
                    for issue in changes:
                        logger.info(f"- JiraNumber: {issue['JiraNumber']}, Title: {issue['JiraTitle']}, Status: {issue['JiraStatus']}, Severity: {issue['Severity']}, Priority: {issue['Priority']}")
                    # Send messages to WebEx rooms for the changed issues
                    IterateThroughListOfMules(changes)
                else:
                    logger.info("No changes detected.")
                
                # Update old_list only if new_list passes completeness validation
                if is_list_complete(new_list, old_list):
                    old_list = new_list
                else:
                    logger.warning("New issue list is incomplete or below threshold; old list not updated.")
            
            except Exception as e:
                logger.error(f"Error during monitoring loop iteration: {e}", exc_info=True)
                
    except Exception as e:
        logger.critical(f"Program stopped due to an unhandled exception: {e}", exc_info=True)
if __name__ == "__main__":
    main()