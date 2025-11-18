import requests
import json
import os

# Define a dictionary to store all WebEx room IDs
WEBEX_ROOM_IDS = {
    'MX': 'Y2lzY29zcGFyazovL3VzL1JPT00vMzMxNjk2NTAtMTNhMy0xMWVmLTk3YTctYjc4MGY3MDE3Y2Vj',
    'MS': 'Y2lzY29zcGFyazovL3VzL1JPT00vOGFlNWZjZTAtMTNhMy0xMWVmLWIxZmMtNjU1NzI5NWRlODFm',
    'MARS': 'Y2lzY29zcGFyazovL3VzL1JPT00vOGFlNWZjZTAtMTNhMy0xMWVmLWIxZmMtNjU1NzI5NWRlODFm',
    'MR': 'Y2lzY29zcGFyazovL3VzL1JPT00vOTM5MDRmODAtMTNhMy0xMWVmLTk5Y2UtNzE4MmVhMmU4MTNm',
    'MV': 'Y2lzY29zcGFyazovL3VzL1JPT00vYWRjNzZlNjAtMTNhMy0xMWVmLWI0ZDItMjk3ZjliY2Q1N2Vl',
    'MT': 'Y2lzY29zcGFyazovL3VzL1JPT00vYWRjNzZlNjAtMTNhMy0xMWVmLWI0ZDItMjk3ZjliY2Q1N2Vl',
    'SM': 'Y2lzY29zcGFyazovL3VzL1JPT00vYTNkZjZiYTAtMTNhMy0xMWVmLTk4YTAtYmZjMWM1Y2FlMmU5',
    'Cloud': 'Y2lzY29zcGFyazovL3VzL1JPT00vOWNlMzNlMzAtMTNhMy0xMWVmLWFiZGItYjU0NzdmZTU5Y2U5',
    'MG': 'Y2lzY29zcGFyazovL3VzL1JPT00vNjUyMzFiZDAtMjgyNy0xMWVmLTkzZTgtZmIwZDgwMmVmM2Rj',
    'Sev1': 'Y2lzY29zcGFyazovL3VzL1JPT00vZTM2ODI2YTAtOWRlNS0xMWVmLWI5MTctMzMwOTg4YmJjY2Q1',
    'TEST': 'Y2lzY29zcGFyazovL3VzL1JPT00vMTNmZjgyZTAtZWUwYS0xMWVlLWFjMzYtZjU3YzlkMDJkYWNi',
    'FRTENG': 'Y2lzY29zcGFyazovL3VzL1JPT00vNGNhMmI0YjAtMjllMC0xMWYwLThkNzUtMDc5NWY5NDUzZWVi',
    'Alpha': 'Y2lzY29zcGFyazovL3VzL1JPT00vMTNmZjgyZTAtZWUwYS0xMWVlLWFjMzYtZjU3YzlkMDJkYWNi'
}

WEBEX_ROOM_IDS_BETA = {
    'MX': 'Y2lzY29zcGFyazovL3VzL1JPT00vNTA4NWNiOTAtYzQwZC0xMWYwLTg4YjktODlmNTM2MWMzYjQx',
    'MS': 'Y2lzY29zcGFyazovL3VzL1JPT00vNzExMjAyNzAtYzQwZC0xMWYwLWIzODctM2Q2ZGExNjcwMWE4',
    'MARS': 'Y2lzY29zcGFyazovL3VzL1JPT00vNzExMjAyNzAtYzQwZC0xMWYwLWIzODctM2Q2ZGExNjcwMWE4',
    'MR': 'Y2lzY29zcGFyazovL3VzL1JPT00vOTIxYTIwMTAtYzQwZC0xMWYwLWEwYTMtYzc4YTM5NzA5ZmZj',
    'MV': 'Y2lzY29zcGFyazovL3VzL1JPT00vYWFlZWVmZDAtYzQwZC0xMWYwLWE2NDItYjNjMzcxMzA0ZDc5',
    'MT': 'Y2lzY29zcGFyazovL3VzL1JPT00vYWFlZWVmZDAtYzQwZC0xMWYwLWE2NDItYjNjMzcxMzA0ZDc5',
    'Cloud': 'Y2lzY29zcGFyazovL3VzL1JPT00vMTNmZjgyZTAtZWUwYS0xMWVlLWFjMzYtZjU3YzlkMDJkYWNi',
    'Sev1': 'Y2lzY29zcGFyazovL3VzL1JPT00vY2Q4M2EwZTAtYzQwZC0xMWYwLWExYzYtZDc3MWU0NWI2ZDNl'
}



def SendMessage(json_data, product_key):
    """
    Sends a message with the given Adaptive Card JSON data to the WebEx room
    associated with the product_key.
    """
    # Default room ID if product_key not found
    default_room_id = WEBEX_ROOM_IDS_BETA.get('Alpha')

    # Handle special cases where multiple keys map to the same room ID
    # For keys with multiple aliases, check explicitly
    if product_key in ('MS', 'MARS'):
        room_id = WEBEX_ROOM_IDS_BETA.get('MS', default_room_id)
    elif product_key in ('MV', 'MT'):
        room_id = WEBEX_ROOM_IDS_BETA.get('MV', default_room_id)
    else:
        room_id = WEBEX_ROOM_IDS_BETA.get(product_key, default_room_id)

    url = 'https://webexapis.com/v1/messages'
    headers = {
        'Authorization': f'Bearer {os.environ["WEBEX_BOT_KEY"]}',
        'Content-Type': 'application/json'
    }
    data = {
        'roomId': room_id,
        'markdown': 'Interactive card:',
        'attachments': [
            {
                'contentType': 'application/vnd.microsoft.card.adaptive',
                'content': json_data
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    # Optional: Add error handling/logging here if needed


def IterateThroughListOfMules(mule_data):
    """
    Iterates through a list of mule issues, composes adaptive cards, and sends messages
    to the appropriate WebEx rooms based on product key and severity.
    """
    for issue in mule_data:
        # Compose the adaptive card message
        message = ComposeAdaptiveCard(
            issue['JiraNumber'],
            issue['JiraStatus'],
            issue['JiraTitle'],
            issue['CaseNumber'],
            issue['MuleLink'],
            issue['Severity']
        )
        
        product_key = issue['Key']
        mule_severity = issue['Severity']
        mule_status = issue['JiraStatus']

        # Send message to the product-specific room
        SendMessage(message, product_key)

        # If severity is 'Severity 1 - Major Impact' and status is 'New', send to Sev1 room as well
        if mule_severity == 'Severity 1 - Major Impact' and mule_status == 'New':
            SendMessage(message, 'Sev1')


def ComposeAdaptiveCard(JiraNumber, Status, Title, CaseNumber, MuleLink, Severity):
    """
    Composes an adaptive card JSON object based on the issue status and severity.
    Loads the appropriate card template, fills in the details, and returns the card.
    """
    # Map statuses to their corresponding card template file paths
    card_files = {
        ('New', 'Severity 1 - Major Impact'): "src/project/cards/mule-created-sev1-card.json",
        ('New', None): "src/project/cards/mule-created-card.json",
        ('Support Pending', None): "src/project/cards/mule-sp-card.json",
        ('Needs Verification', None): "src/project/cards/mule-nv-card.json",
        ('Closed', None): "src/project/cards/mule-closed-card.json"
    }

    # Determine which card file to load
    card_file = None
    if Status == 'New' and Severity == 'Severity 1 - Major Impact':
        card_file = card_files[('New', 'Severity 1 - Major Impact')]
    elif Status == 'New':
        card_file = card_files[('New', None)]
    else:
        # Try to find a card file matching the status, ignoring severity
        card_file = card_files.get((Status, None))

    if not card_file:
        return "Something must have gone wrong Here"

    # Load the card template JSON
    with open(card_file, "r") as card_json_file:
        card = json.load(card_json_file)

    # Convert MuleLink and CaseNumber to strings to handle possible None or NaN values
    str_mule_link = str(MuleLink)
    str_case_number = str(CaseNumber)

    # Fill in the facts in the card body
    facts = card['body'][1]['facts']
    facts[0]['value'] = f'[{JiraNumber}](https://meraki.atlassian.net/browse/{JiraNumber})'
    facts[1]['value'] = f'[{str_case_number}](https://meraki.my.salesforce.com/{str_mule_link})'
    facts[2]['value'] = Title
    facts[3]['value'] = Severity

    return card


