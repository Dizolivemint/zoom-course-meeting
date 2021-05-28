import csv
import http.client
import json
from os import close
import jwt
from datetime import datetime, timedelta
import time
from typing import NamedTuple, Dict, Union, cast
import argparse

API_KEY_KEY = 'api_key'
API_SECRET_KEY = 'api_secret'
TOKEN = 'token'
URL = 'url'

Creds = NamedTuple('Creds', [('key', str), ('secret', str), ('url', str), ('token', str)])

# Open Schedule CSV
# ---Start---
def read_csv(filename: str):
    meetings = []
    with open(filename, newline='') as csvfile:
        meeting_reader = csv.reader(csvfile, dialect='excel', delimiter=',', quotechar='|')
        next(meeting_reader)
        for row in meeting_reader:
            meetings.append({
                'meetingId': row[0],
                'meeting': row[1],
                'schedule_for': row[2],
                'topic': row[3],
                'start_time': row[4],
                'duration': int(row[5]),
                'timezone': row[6],
                'agenda': row[7],
                'settings': {
                    'host_video': row[8] == 'TRUE',
                    'participants_video': row[9] == 'TRUE',
                    'join_before_host': row[10] == 'TRUE',
                    'jbh_time': int(row[11]),
                    'mute_upon_entry': row[12] == 'TRUE',
                    'approval_type': int(row[13]),
                    'registration_type': int(row[14]),
                    'auto_recording': row[15],
                    'waiting_room': row[16] == 'TRUE',
                    'contact_name': row[17],
                    'contact_email': row[18],
                    'registrants_confirmation_email': row[19] == 'TRUE',
                    'registrants_email_notification': row[20] == 'TRUE',
                    'meeting_authentication': row[21] == 'TRUE',
                    # 'authentication_domains': row[22],
                    'show_share_button': row[23] == 'TRUE',
                    'allow_multiple_devices': row[24] == 'TRUE',
                    'alternative_hosts_email_notification': row[25] == 'TRUE'
                }
            })
            
        # TODO remove empty meetings    
        # for meeting in list(meetings):
        #     print(meeting)
                    
    return meetings
# ---End---

# Read and process credentials
# ---Start---
def read_credentails() -> Creds:
    raw_creds: Dict[str, str] = {}
    with open('zoom_creds', 'r') as cred_file:
        for line in cred_file.readlines():
            (key, value) = line.strip().split('=')
            raw_creds[key] = value

    key = raw_creds[API_KEY_KEY]
    secret = raw_creds[API_SECRET_KEY]
    url = raw_creds[URL]
    token = raw_creds[TOKEN]
    
    return Creds(key, secret, url, token)

def generate_jwt(key: str, secret: str) -> str:
    expiry = datetime.utcnow() + timedelta(minutes=15)
    unix_expiry = expiry.timestamp()
    payload: Dict[str, str] = {'iss': key, 'exp': unix_expiry}
    encoded_jwt = jwt.encode(payload, secret, algorithm='HS256')
    
    return encoded_jwt

def json_to_dict(res) -> dict:
    data_json = res.read().decode('utf-8')
    data: Dict[str, Union[str, int]] = json.loads(data_json)
    
    return data
# ---End---

# Update Meeting
# ---Start--- #
def update_meeting_request(valid_jwt: str, meeting: dict, meeting_id: str) -> str:
    data = {}
    conn = http.client.HTTPSConnection('api.zoom.us')
    headers = {
		'authorization': f'Bearer {valid_jwt}',
		'content-type': 'application/json'
	}

    try:    
        conn.request('PATCH', f'/v2/meetings/{meeting_id}', body=json.dumps(meeting), headers=headers)
        res = conn.getresponse()
        print(res.status, res.read())
        data = json_to_dict(res)
    except Exception as x:
        data = { 'topic': f'Error {x} occured on call to update meeting' }
        
    # Error check if there is an issue finding the user
    if 'code' in data:
        data = { 'topic': f'Error: {data["message"]} occured on call to update meeting' }

    return cast(str, data['topic'])
# ---End---

# Update Webinar
# ---Start--- #
def update_webinar_request(valid_jwt: str, meeting: dict, meeting_id: str) -> str:
    data = {}
    conn = http.client.HTTPSConnection('api.zoom.us')
    headers = {
		'authorization': f'Bearer {valid_jwt}',
		'content-type': 'application/json'
	}
    
    try:    
        conn.request('PATCH', f'/v2/webinars/{meeting_id}', body=json.dumps(meeting), headers=headers)
        res = conn.getresponse()
        print(res.status, res.read())
        data = json_to_dict(res)
    except Exception as x:
        data = { 'topic': f'Error {x} occured on call to update webinar' }
        
    # Error check if there is an issue finding the user
    if 'code' in data:
        data = { 'topic': f'Error: {data["message"]} occured on call to update webinar' }

    return cast(str, data['topic'])
# ---End---
        
# Store Meeting ID and Course ID
# ---Start---
def store_data(lti_csv: list, meeting_id: str, course_id: str) -> list:
    lti_csv.append([
        meeting_id,
        course_id,
        'https://elearning.pacificcollege.edu'
    ])
    
    return lti_csv
# ---End---

# Write CSV for Zoom LTI (Meeting ID and Moodle Course ID)
# ---Start---
def write_csv(lti_csv: list, out_filename: str) -> bool:
    with open(out_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Meeting ID', 'Context ID', 'Domain'])

        for lti in lti_csv:
            writer.writerow(lti)
    
    csvfile.close()
    
    return True
# ---End---

# Store Log Data
# ---Start---
def log_data(log_csv: list, meeting_id: str, meeting_update_response: str) -> list:
    log_csv.append([
        meeting_id,
        meeting_update_response
    ])
    
    return log_csv
# ---End---

# Write CSV for Zoom LTI (Meeting ID and Moodle Course ID)
# ---Start---
def write_log(log_csv: list, out_filename: str) -> bool:
    with open(out_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for log in log_csv:
            writer.writerow(log)
    
    csvfile.close()
    
    return True
# ---End---

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backs up Zoom cloud recordings')
    parser.add_argument(
        '--file',
        metavar='CSV_FILE',
        required=True,
        help='CSV file of meeting settings'
    )
    args = parser.parse_args()
    
    # Create JWT
    key, secret, url, token = read_credentails()
    new_jwt = generate_jwt(key, secret)

    # Read Schedule
    meetings = read_csv(args.file)
    
    # Create a list and log to write to CSV
    lti_csv = []
    log_csv = []
    
    # Loop through schedule
    for body in meetings:
        
        # Set meeting ID and remove it from the request body
        meeting_id = body['meetingId']
        del body['meetingId']
        
        # Set whether meeting and remove it from the request body
        meeting = body['meeting']
        del body['meeting']
        del body['agenda']
        del body['schedule_for']
        
        if meeting == 'TRUE':
            print(f"Updating Meeting: {meeting_id} | {body['topic']}")
            topic = update_meeting_request(new_jwt, body, meeting_id)
        else:
            print(f"Updating Webinar: {meeting_id} | {body['topic']}")
            topic = update_webinar_request(new_jwt, body, meeting_id)
            
        print()
    
        # Log created meeting, course ID, and shortname for reference if the meeting has been created
        log_csv = log_data(log_csv, meeting_id, topic)
        
    if write_log(log_csv, f'update-log-{time.time()}.csv'):
        print(f'File successfully created!')
    else:
        print(f'Error writting log file!')