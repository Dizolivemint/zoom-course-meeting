import csv
import http.client
import json
import jwt
from datetime import datetime, timedelta
from typing import NamedTuple, Dict, Union, cast

API_KEY_KEY = 'api_key'
API_SECRET_KEY = 'api_secret'

Creds = NamedTuple('Creds', [('key', str), ('secret', str)])

# Open Schedule CSV
# ---Start---
def read_csv():
    meetings = []
    with open('schedule.csv', newline='') as csvfile:
        meeting_reader = csv.reader(csvfile, dialect='excel', delimiter=',', quotechar='|')
        for row in meeting_reader:
            # print(', '.join(row))
            meetings.append({
                'topic': f'{row[0].rstrip()}',
                'meeting_type': '2',
                'start_time': f'{row[1]}',
                'duration': f'{row[2]}',
                'schedule_for': f'{row[3]}',
                'timezone': f'{row[4]}',
                'week_days': f'{row[5]}',
                'recurrence_type': '2',
                'end_date_time': f'{row[6]}'
            })

    return meetings

# ---End---

def read_credentails() -> Creds:
    raw_creds: Dict[str, str] = {}
    with open('zoom_creds', 'r') as cred_file:
        for line in cred_file.readlines():
            (key, value) = line.strip().split('=')
            raw_creds[key] = value

    key = raw_creds[API_KEY_KEY]
    secret = raw_creds[API_SECRET_KEY]
    
    return Creds(key, secret)

def generate_jwt(key: str, secret: str) -> str:
    expiry = datetime.utcnow() + timedelta(minutes=15)
    print(expiry)
    unix_expiry = expiry.timestamp()
    print(unix_expiry)
    payload: Dict[str, str] = {'iss': key, 'exp': unix_expiry}
    encoded_jwt = jwt.encode(payload, secret, algorithm='HS256')
    return encoded_jwt

def json_to_dict(res) -> dict:
    data_json = res.read().decode('utf-8')
    print(data_json)
    data: Dict[str, Union[str, int]] = json.loads(data_json)
    return data

# Create New Meeting
# ---Start--- #
def new_meeting_request(valid_jwt: str, meeting: dict) -> str:
    conn = http.client.HTTPSConnection('api.zoom.us')
    headers = {
		'authorization': f'Bearer {valid_jwt}',
		'content-type': 'application/json'
	}
    
    meeting = {'topic': 'Introduction to Kinesiology - BT257.01.2021S.SD', 'meeting_type': '2', 'start_time': '2021-05-03T13:30:00.000Z', 'duration': '195', 'schedule_for': 'mexner@pacificcollege.edu', 'timezone': 'America/Los_Angeles', 'week_days': '2', 'recurrence_type': '2', 'end_date_time': '2021-08-15T23:59:59Z'}
    
    conn.request('GET', f'/v2/users/{meeting["schedule_for"]}', body=None, headers=headers)
    res = conn.getresponse()
    data = json_to_dict(res)
    user_id = cast(str, data['id'])
    
    conn.request('POST', f'/v2/users/{user_id}/meetings', body=json.dumps(meeting), headers=headers)
    res = conn.getresponse()
    data = json_to_dict(res)
    
    return cast(str, data['join_url'])
# ---End---


# Fetch Course ID
# ---Start---
def fetch_course_id(shortname: str) -> str:
    conn = http.client.HTTPSConnection(moodle_url)
    headers = {
		'content-type': 'application/json'
	}
    body = {
        'wstoken': 'token',
        'wsfunction': 'functionName',
        'moodlewsrestformat': 'json',
        'field': 'shortname',
        'value': shortname
    }
    
    conn.request('POST', f'/v2/users/{user_id}/meetings', body=json.dumps(meeting), headers=headers)
    res = conn.getresponse()
    data = json_to_dict(res)
    
    return cast(str, data['id'])
# ---End---
        
# Store Meeting ID and Course ID
# ---Start---
# lti_csv = []
# lti_csv.append({
#     'meeting_id': meeting_id,
#     'course_id': course_id,
#     'meeting_url': meeting_url
# })
# ---End---

# Write CSV for Zoom LTI (Meeting ID and Moodle Course ID)
# ---Start---
# with open(out_filename, 'w', newline='') as csvfile:
#     writer = csv.writer(csvfile, delimiter=',',
#                             quotechar='|', quoting=csv.QUOTE_MINIMAL)
#     writer.writerow(['Meeting ID', 'Course ID'])
# ---End---

if __name__ == '__main__':
    # Create JWT
    key, secret = read_credentails()
    new_jwt = generate_jwt(key, secret)

    # Read Schedule
    meetings = read_csv()
    for body in meetings:
        print(body)
        # Create Meeting or TODO: Check if meeting exists and Update meeting
        join_url = new_meeting_request(new_jwt, body)
        print(join_url)
        
