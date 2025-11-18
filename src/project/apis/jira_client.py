import os
import json
import requests
from requests.auth import HTTPBasicAuth
import time


def fetch_all_mule_issues_with_token():
    """
    Queries the JIRA API for all 'mule' type issues with specific statuses,
    handling pagination using nextPageToken until all pages are retrieved.
    Returns a list of dictionaries containing relevant issue details.
    """
    url = "https://meraki.atlassian.net/rest/api/3/search/jql"
    auth = HTTPBasicAuth(os.environ['JIRA_USER'], os.environ['JIRA_KEY'])
    headers = {"Accept": "application/json"}
    jql_query = (
        'type = mule AND ((status = "Needs Verification" or status = "closed" or status = "Support Pending") OR (status = "New" AND statusCategoryChangedDate!= null) ) and statusCategoryChangedDate >= -100d order by statusCategoryChangedDate'
    )
    max_results_per_page = 50
    all_issues = []
    next_page_token = None
    is_last = False
    page_count = 0

    print("Starting fetch_all_mule_issues_with_token function...")

    while not is_last:
        page_count += 1
        query_params = {
            'jql': jql_query,
            'fields': '*all',
            'maxResults': max_results_per_page
        }
        if next_page_token:
            query_params['nextPageToken'] = next_page_token

        try:
            response = requests.get(url, headers=headers, params=query_params, auth=auth)
            response.raise_for_status()
            response_json = response.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Failed to fetch or parse JIRA issues on page {page_count}: {e}")
            break

        issues = response_json.get('issues', [])
        for idx, issue in enumerate(issues, start=1):
            fields = issue.get('fields', {})
            severity_field = fields.get('customfield_10287')
            severity_value = severity_field.get('value') if severity_field else 'No Severity'

            issue_data = {
                'JiraNumber': issue.get('key'),
                'JiraTitle': fields.get('summary'),
                'JiraStatus': fields.get('status', {}).get('name'),
                'CaseNumber': fields.get('customfield_10271'),
                'MuleLink': fields.get('customfield_10419'),
                'Key': fields.get('project', {}).get('key'),
                'Severity': severity_value
            }
            all_issues.append(issue_data)

        # Update pagination tokens
        next_page_token = response_json.get('nextPageToken')
        is_last = response_json.get('isLast', True)  # Default to True if not present

    print(f"Finished fetching issues. Total issues retrieved: {len(all_issues)}")
    return all_issues




def compare_issue_lists(old_list, new_list):
    """
    Compares two lists of issue dictionaries and returns a list of issues that are either:
    - New in the new_list (not present in old_list by JiraNumber)
    - Changed in the new_list compared to old_list (any field differs)
    Additionally, prints out what changes were found.
    """
    old_issues_map = {issue['JiraNumber']: issue for issue in old_list}
    changes = []

    for new_issue in new_list:
        jira_num = new_issue['JiraNumber']
        old_issue = old_issues_map.get(jira_num)
        if not old_issue:
            # New issue
            print(f"New issue detected: {jira_num}")
            changes.append(new_issue)
        else:
            # Check if any field has changed
            changed_fields = []
            for key in new_issue:
                old_value = old_issue.get(key)
                new_value = new_issue.get(key)
                if old_value != new_value:
                    changed_fields.append((key, old_value, new_value))
            if changed_fields:
                print(f"Issue {jira_num} has changed fields:")
                for field, old_val, new_val in changed_fields:
                    print(f" - {field}: '{old_val}' -> '{new_val}'")
                changes.append(new_issue)
    return changes


