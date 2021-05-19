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
    with open('mdl-zoom-2020-420-901.csv', newline='') as csvfile:
        meeting_reader = csv.reader(csvfile, dialect='excel', delimiter=',', quotechar='|')
        next(meeting_reader)
        for row in meeting_reader:
            meetings.append({
                'id': f'{row[0].rstrip()}',
                'course_id': f'{row[1].rstrip()}'
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

# Get Meeting Participants
# ---Start--- #
def get_meeting_request(valid_jwt: str, meeting: dict) -> str:
    data = {}
    conn = http.client.HTTPSConnection('api.zoom.us')
    headers = {
		'authorization': f'Bearer {valid_jwt}',
		'content-type': 'application/json'
	}
    try:
        conn.request('GET', f'/v2/meetings/{meeting["id"]}', body=None, headers=headers)
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = { 'uuid': f'Error: {x} occured on call to fetch user' }
        return cast(str, data['uuid'])

    # Error check if there is an issue finding the user
    if 'code' in data:
        data = { 'uuid': f'Error: {data["message"]} occured on call to get meeting' }

    return cast(str, data['uuid'])
# ---End---

# Get Meeting Participants
# ---Start--- #
def get_meeting_participants_report_request(valid_jwt: str, meeting: dict) -> str:
    data = {}
    conn = http.client.HTTPSConnection('api.zoom.us')
    headers = {
		'authorization': f'Bearer {valid_jwt}',
		'content-type': 'application/json'
	}
    print('________________________')
    print('Meeting: ' + meeting["id"])
    try:
        conn.request('GET', f'/v2/report/meetings/{meeting["id"]}/participants?page_size=300', body=None, headers=headers)
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = { 'participants': f'Error: {x} occured on call to fetch user' }
        return cast(str, data['participants'])

    # Error check if there is an issue finding the user
    if 'code' in data:
        data = { 'participants': f'Error: {data["message"]} occured on call to get participants' }

    return cast(str, data['participants'])
# ---End---


# Fetch Course
# ---Start---
def fetch_course(course_id: str, url: str, token: str) -> str:
    conn = http.client.HTTPSConnection(url)
    function = 'core_course_get_courses'
    body = { 
            "options": {
                "ids": [course_id]
            }
        }
    try:
        conn.request('GET', f'/webservice/rest/server.php?wstoken={token}&wsfunction={function}&moodlewsrestformat=json&options[ids][0]={course_id}', body=None, headers={})
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = [{ 
                'shortname': f'{x}'
               }]
    if 'exception' in data:
        data = [{ 
                'shortname': f'{data["message"]}'
               }]
    return data[0]['shortname']
# ---End---

# Fetch Course Users
# ---Start---
def fetch_course_users(course_id: str, url: str, token: str) -> str:
    conn = http.client.HTTPSConnection(url)
    function = 'core_enrol_get_enrolled_users'
    body = { 
            "courseid": course_id
        }
    try:
        conn.request('GET', f'/webservice/rest/server.php?wstoken={token}&wsfunction={function}&moodlewsrestformat=json&courseid={course_id}', body=None, headers={})
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = [{ 
                'email': f'{x}'
               }]
    if 'exception' in data:
        data = [{ 
                'email': f'{data["message"]}'
               }]
    
    return data
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
def log_data(log_csv: list, meeting_id: str, course_id: str, shortname: str) -> list:
    log_csv.append([
        shortname,
        meeting_id,
        course_id
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
        course_name = fetch_course(body['course_id'], url, token)
        enrolled_user = []
        meeting_attendee = []
        # Get enrolled users from Moodle
        users = fetch_course_users(body['course_id'], url, token)
        
        print('______________________')
        print(course_name)
        print(f'Course ID: {body["course_id"]}')
        print('______________________')
        
        for user in users:
            print(f'Enrolled User: {user["email"]}')
            enrolled_user.append(user["email"])
        
        
        
        # Get participants from Zoom Meeting
        participants = get_meeting_participants_report_request(new_jwt, body)
        for participant in participants:
            print(f'Meeting Participant: {participant["user_email"]}')
            # print(f'join_time: {participant["join_time"]}')
            # print(f'leave_time: {participant["leave_time"]}')
            meeting_attendee.append(participant["user_email"])
            
        # Compare emails and log students that did not attend
        filtered = [email for email in enrolled_user if email not in meeting_attendee]
        print(f'Absent: {filtered}')
        
        # Compare join and leave time to course start and end time?
        # Get course duration
        
        
    #     # Log created meeting, course ID, and shortname for reference if the meeting has been created
    #     log_csv = log_data(log_csv, meeting_id, course_id, shortname)
    
    # if write_csv(lti_csv, f'mdl-zoom{time.time()}.csv'):
    #     print(f'File successfully created!')
    # else:
    #     print(f'Error writting CSV file!')
        
    # if write_log(log_csv, f'log{time.time()}.csv'):
    #     print(f'File successfully created!')
    # else:
    #     print(f'Error writting log file!')