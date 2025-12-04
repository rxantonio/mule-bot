import os
import json
import requests
from requests.auth import HTTPBasicAuth
import time



def get_jira_issue(issue_key):
    """
    Fetches issue details from the JIRA API for the given issue key using HTTP Basic Authentication.

    Args:
        issue_key (str): The JIRA issue key (e.g., "SM-7789").

    Returns:
        dict: Parsed JSON response of the issue details if successful.
        None: If there was an error during the request.
    """
    url = f"https://meraki.atlassian.net/rest/api/3/issue/{issue_key}"
    auth = HTTPBasicAuth(os.environ['JIRA_USER'], os.environ['JIRA_KEY'])
    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, auth=auth, timeout=10)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred while fetching issue {issue_key}: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"Connection error occurred while fetching issue {issue_key}: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"Timeout error occurred while fetching issue {issue_key}: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"An error occurred while fetching issue {issue_key}: {req_err}")
    except ValueError as json_err:
        print(f"Error decoding JSON response for issue {issue_key}: {json_err}")

    return None



def pretty_print_json(data_dict):
    """
    Pretty prints a dictionary as formatted JSON.
    """
    print(json.dumps(data_dict, indent=4, sort_keys=True))

def extract_text_from_content(content):
    """
    Recursively extracts text from Atlassian document format content blocks,
    including paragraphs, ordered lists, and other nested elements.
    """
    texts = []

    for block in content:
        block_type = block.get('type')
        if block_type == 'paragraph':
            # Extract text from paragraph content
            for item in block.get('content', []):
                if item.get('type') == 'text':
                    texts.append(item.get('text', ''))
        elif block_type == 'orderedList':
            # Extract text from each list item recursively
            for list_item in block.get('content', []):
                # Each list_item is a listItem block
                item_texts = extract_text_from_content(list_item.get('content', []))
                # Prefix with list number or bullet (optional)
                texts.append('• ' + ' '.join(item_texts))
        elif block_type == 'listItem':
            # Extract text from list item content recursively
            item_texts = extract_text_from_content(block.get('content', []))
            texts.append(' '.join(item_texts))
        else:
            # For other block types, recursively extract if they have content
            if 'content' in block:
                texts.extend(extract_text_from_content(block['content']))

    return texts

def human_readable_issue_summary(issue_json):
    """
    Extracts and prints key information from a JIRA issue JSON response
    in a human-readable format, showing the full description including ordered lists.
    """
    fields = issue_json.get('fields', {})

    # Basic info
    issue_key = issue_json.get('key', 'N/A')
    summary = fields.get('summary', 'N/A')
    status = fields.get('status', {}).get('name', 'N/A')
    priority = fields.get('priority', {}).get('name', 'N/A')
    assignee = fields.get('assignee', {}).get('displayName', 'Unassigned')
    reporter = fields.get('reporter', {}).get('displayName', 'N/A')
    created = fields.get('created', 'N/A')
    updated = fields.get('updated', 'N/A')
    resolution = fields.get('resolution', {}).get('name', 'Unresolved')

    # Description extraction with full content including ordered lists
    description = fields.get('description')
    description_text = "N/A"
    if isinstance(description, dict):
        content = description.get('content', [])
        texts = extract_text_from_content(content)
        description_text = ''.join(texts).strip() if texts else "N/A"
    elif isinstance(description, str):
        description_text = description.strip()

    # Print formatted summary with full description
    print(f"Issue Key: {issue_key}")
    print(f"Summary: {summary}")
    print(f"Status: {status}")
    print(f"Priority: {priority}")
    print(f"Assignee: {assignee}")
    print(f"Reporter: {reporter}")
    print(f"Created: {created}")
    print(f"Updated: {updated}")
    print(f"Resolution: {resolution}")
    print("Description:")
    print(description_text)