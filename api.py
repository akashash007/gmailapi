import os
import json
import pytz
import pprint
import base64
import mysql.connector
from datetime import datetime
from email import message_from_bytes
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError as RequestError

# Set up the Gmail API client
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
creds = None
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

service = build('gmail', 'v1', credentials=creds)

# Set up the database connection
conn = mysql.connector.connect(
    host="localhost",
    user="myusername",
    password="mypassword",
    database="gmail"
)
cur = conn.cursor()

# Fetch a list of emails from the Inbox
results = service.users().messages().list(userId='me', q='in:inbox').execute()
messages = results.get('messages', [])

def mark_as_read(service, message_id):
    """Marks a message as read given its message ID."""
    message_labels = {'removeLabelIds': ['UNREAD'], 'addLabelIds': []}
    try:
        service.users().messages().modify(userId='me', id=message_id, body=message_labels).execute()
        print(f'Message with ID: {message_id} marked as read.')
    except Exception as e:
        print(f'An error occurred: {e}')

# create a check list for emails from the Inbox
def check_email_rules(email_data, rules):
    for rule in rules:
        if rule['predicate'] == 'All':
            condition_met = True
            for condition in rule['conditions']:
                if condition['field'] == 'from':
                    if condition['predicate'] == 'contains' and condition['value'] not in email_data['from']:
                        condition_met = False
                    elif condition['predicate'] == 'not equals' and condition['value'] == email_data['from']:
                        condition_met = False
                elif condition['field'] == 'To':
                    if condition['predicate'] == 'contains' and condition['value'] not in email_data['to']:
                        condition_met = False
                    elif condition['predicate'] == 'not equals' and condition['value'] == email_data['to']:
                        condition_met = False
                elif condition['field'] == 'Subject':
                    if condition['predicate'] == 'contains' and condition['value'] not in email_data['subject']:
                        condition_met = False
                    elif condition['predicate'] == 'not equals' and condition['value'] == email_data['subject']:
                        condition_met = False
                elif condition['field'] == 'Body':
                    if condition['predicate'] == 'contains' and condition['value'] not in email_data['body']:
                        condition_met = False
                    elif condition['predicate'] == 'not equals' and condition['value'] == email_data['body']:
                        condition_met = False
            if condition_met:
                return True
    return False


# Store these emails in a database table
for msg in messages:
    msg_bytes = service.users().messages().get(userId='me', id=msg['id']).execute()
    pprint.pprint(msg_bytes) # Removed the encoding parameter
    if 'raw' in msg_bytes:
        email = message_from_bytes(msg_bytes['raw'].encode('utf-8'))
    else:
        payload = msg_bytes['payload']
        if isinstance(payload, dict) and 'parts' in payload:
            email_data = payload['parts'][0]['body']['data']
        else:
            email_data = payload['body']['data']
        email = message_from_bytes(base64.urlsafe_b64decode(email_data))
    email_data = {}
    for header in email._headers:
        if header[0] == 'from':
            email_data['from'] = header[1]
        elif header[0] == 'to':
            email_data['to'] = header[1]
        elif header[0] == 'subject':
            email_data['subject'] = header[1]
        elif header[0] == 'date':
            try:
                email_date = datetime.strptime(header[1][:-6], '%a, %d %b %Y %H:%M:%S')
                email_date = pytz.timezone('UTC').localize(email_date)
                email_data['received'] = email_date.astimezone(pytz.timezone('Asia/Kolkata'))
            except Exception as e:
                print(e)
        elif header[0] == 'Message-ID':
            email_data['message_id'] = header[1]
        elif header[0] == 'In-Reply-To':
            email_data['in_reply_to'] = header[1]
        elif header[0] == 'References':
            email_data['references'] = header[1]
        elif header[0] == 'Content-Type':
            email_data['content_type'] = header[1]

            try:
                email_date = datetime.strptime(header[1][:-6], '%a, %d %b %Y %H:%M:%S')
                email_date = pytz.timezone('UTC').localize(email_date)
                email_data['received'] = email_date.astimezone(pytz.timezone('Asia/Kolkata'))
            except Exception as e:
                print(e)

    # Insert email data into a database table
    if 'from' in email_data:
        from_email = email_data['from']
    else:
        from_email = ''
    if 'to' in email_data:
        to_email = email_data['to']
    else:
        to_email = ''
    if 'subject' in email_data:
        subject = email_data['subject']
    else:
        subject = ''
    if 'received' in email_data:
        received = email_data['received']
    else:
        received = ''
    
    #  create a query for inserting email details into MySQL table
    insert_query = f"INSERT INTO emails (from_email, to_email, subject, received) VALUES ('{email_data['from']}', '{email_data['to']}', '{email_data['subject']}', '{email_data['received']}')"
    cur.execute(insert_query)
    conn.commit()

    # Mark the email as read
    mark_as_read(service, msg['id'])

# Close the database connection
conn.close()
