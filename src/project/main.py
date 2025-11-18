from apis.jira_client import fetch_all_mule_issues_with_token, compare_issue_lists
from apis.webex_client import IterateThroughListOfMules
import time


def main():
    print("Starting continuous issue monitoring loop...")
    old_list = fetch_all_mule_issues_with_token()
    print(f"Initial fetch complete. Retrieved {len(old_list)} issues.")
    
    while True:
        print("Waiting 1 minute before next fetch...")
        time.sleep(60)  # Wait 1 minute
        
        print("Fetching new list of issues...")
        new_list = fetch_all_mule_issues_with_token()
        print(f"New fetch complete. Retrieved {len(new_list)} issues.")
        
        print("Comparing old and new issue lists for changes...")
        changes = compare_issue_lists(old_list, new_list)
        
        if changes:
            print(f"Detected {len(changes)} new or changed issues:")
            for issue in changes:
                print(f"- JiraNumber: {issue['JiraNumber']}, Title: {issue['JiraTitle']}, Status: {issue['JiraStatus']}, Severity: {issue['Severity']}")
            # Send messages to WebEx rooms for the changed issues
            IterateThroughListOfMules(changes)
        else:
            print("No changes detected.")
        
        # Update old_list to the new_list for the next iteration
        old_list = new_list


if __name__ == "__main__":
    main()