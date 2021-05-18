import csv
import http.client
import json
import jwt
from datetime import datetime, timedelta
import time
from typing import NamedTuple, Dict, Union, cast

API_KEY_KEY = 'api_key'
API_SECRET_KEY = 'api_secret'
TOKEN = 'token'
URL = 'url'

Creds = NamedTuple('Creds', [('key', str), ('secret', str), ('url', str), ('token', str)])

# Open Schedule CSV
# ---Start---
def read_csv():
    meetings = []
    with open('schedule_meeting.csv', newline='') as csvfile:
        meeting_reader = csv.reader(csvfile, dialect='excel', delimiter=',', quotechar='|')
        for row in meeting_reader:
            meetings.append({
                'topic': f'{row[0].rstrip()}',
                'type': 2,
                'start_time': f'{row[1]}',
                'duration': f'{row[2]}',
                'schedule_for': f'{row[3]}',
                'timezone': f'{row[4]}',
                'settings': {
                    'host_video': 'false',
                    'join_before_host': 'true',
                    'jbh_time': 15,
                    'mute_upon_entry': 'true',
                    'approval_type': 0,
                    'registration_type': 1
                }
            })

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

# Create New Meeting
# ---Start--- #
def new_meeting_request(valid_jwt: str, meeting: dict) -> str:
    data = {}
    conn = http.client.HTTPSConnection('api.zoom.us')
    headers = {
		'authorization': f'Bearer {valid_jwt}',
		'content-type': 'application/json'
	}
    try:
        conn.request('GET', f'/v2/users/{meeting["schedule_for"]}', body=None, headers=headers)
        res = conn.getresponse()
        data = json_to_dict(res)
        user_id = cast(str, data['id'])
    except Exception as x:
        data = { 'id': f'Error: {x} occured on call to fetch user' }
        return cast(str, data['id'])

    try:    
        conn.request('POST', f'/v2/users/{user_id}/meetings', body=json.dumps(meeting), headers=headers)
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = { 'id': f'Error {x} occured on call to create meeting' }
        
    # Error check if there is an issue finding the user
    if 'code' in data:
        data = { 'id': f'Error: {data["message"]} occured on call to create meeting' }

    return cast(str, data['id'])
# ---End---
        
# Store Meeting ID and Course ID
# ---Start---
def store_data(lti_csv: list, meeting_id: str) -> list:
    lti_csv.append([
        meeting_id
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
def log_data(log_csv: list, meeting_id: str, topic: str) -> list:
    log_csv.append([
        topic,
        meeting_id
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
    # Create JWT
    key, secret, url, token = read_credentails()
    new_jwt = generate_jwt(key, secret)

    # Read Schedule
    meetings = read_csv()
    
    # Create a list and log to write to CSV
    lti_csv = []
    log_csv = []
    
    # Loop through schedule
    for body in meetings:
        
        # Set meeting id to None for log, in case of error
        meeting_id = 'None'
            
        print(f'Creating Meeting: {body["topic"]}')
        # Create Meeting or TODO: Check if meeting exists and Update meeting

        meeting_id = new_meeting_request(new_jwt, body)
        print(f'Meeting ID: {meeting_id}')
        
        # Log created meeting, name for reference if the meeting has been created
        log_csv = log_data(log_csv, meeting_id, body["topic"])
    
    if write_csv(lti_csv, f'mdl-zoom{time.time()}.csv'):
        print(f'File successfully created!')
    else:
        print(f'Error writting CSV file!')
        
    if write_log(log_csv, f'log{time.time()}.csv'):
        print(f'File successfully created!')
    else:
        print(f'Error writting log file!')