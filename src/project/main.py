from apis.jira_client import fetch_all_mule_issues_with_token, compare_issue_lists
from apis.webex_client import IterateThroughListOfMules
import time
from utils.logger import setup_logger
import utils.seed_issues
import importlib


# from services.jira_service import get_jira_issue, pretty_print_json, human_readable_issue_summary
# response_data=get_jira_issue('SM-7789')
# human_readable_issue_summary(response_data)

logger = setup_logger(__name__)

def is_list_complete(new_list, old_list, min_expected=10, completeness_ratio=0.8): 
    # Check minimum expected number of issues CHANGE THIS BACK TO 100 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if len(new_list) < min_expected:
        return False
    
    
    # Check size ratio compared to old_list
    if old_list and len(new_list) < len(old_list) * completeness_ratio:
        return False
    
    return True

def get_issues(use_seed=False):
    """
    Returns the list of issues.
    If use_seed is True, returns the seed data.
    Otherwise, fetches real data from the JIRA API.
    """
    if use_seed:
        importlib.reload(utils.seed_issues)  # Reload seed_data module to get latest changes
        logger.info("Using seed data for issues.")
        return utils.seed_issues.seed_data
    else:
        logger.info("Fetching real data from JIRA API.")
        return fetch_all_mule_issues_with_token()


def main(use_seed=False):
    logger.info("Starting continuous issue monitoring loop...")
    
    try:
        old_list = get_issues(use_seed=use_seed)
        logger.info(f"Initial fetch complete. Retrieved {len(old_list)} issues.")
        
        while True:
            try:
                logger.info("Waiting...")
                time.sleep(60)  # Wait 1 minute
                
                new_list = get_issues(use_seed=use_seed)
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
    # Set use_seed=True to test with seed data, False for real data
    main(use_seed=False)