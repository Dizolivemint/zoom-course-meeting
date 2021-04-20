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
    with open('schedule.csv', newline='') as csvfile:
        meeting_reader = csv.reader(csvfile, dialect='excel', delimiter=',', quotechar='|')
        for row in meeting_reader:
            meetings.append({
                'shortname': f'{row[1].rstrip()}',
                'topic': f'{row[0].rstrip()}' + ' - ' + f'{row[1].rstrip()}',
                'type': 8,
                'start_time': f'{row[2]}',
                'duration': f'{row[3]}',
                'schedule_for': f'{row[4]}',
                'timezone': f'{row[5]}',
                'recurrence': {
                    'type': 2,
                    'repeat_interval': 1,
                    'weekly_days': f'{row[6]}',
                    'end_date_time': f'{row[7]}'
                },
                'settings': {
                    'join_before_host': 'true',
                    'jbh_time': 10,
                    'mute_upon_entry': 'true',
                    'meeting_authentication': 'true',
                    'authentication_domains': 'pacificcollege.edu'
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
        data['id'] = f'Exception {x} occured on call'
        return cast(str, data['id'])
        
    conn.request('POST', f'/v2/users/{user_id}/meetings', body=json.dumps(meeting), headers=headers)
    res = conn.getresponse()
    data = json_to_dict(res)

    return cast(str, data['id'])
# ---End---


# Fetch Course ID
# ---Start---
def fetch_course_id(shortname: str, url: str, token: str) -> str:
    conn = http.client.HTTPSConnection(url)
    function = 'core_course_get_courses_by_field'
    try:
        conn.request('GET', f'/webservice/rest/server.php?wstoken={token}&wsfunction={function}&moodlewsrestformat=json&field=shortname&value={shortname}', body=None, headers={})
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = { 
                'courses': {
                    0: {
                        'id': f'Error: {x} occured on {shortname}'
                    }
                }
               }
    if 'exception' in data:
        data = { 
                'courses': {
                    0: {
                        'id': f'Error: {data["message"]} occured on {shortname}'
                    }
                }
               }
    if data['courses'] == []:
        data = { 
                'courses': {
                    0: {
                        'id': 'Error: Course does not exist'
                    }
                }
               }    
    return cast(str, data['courses'][0]['id'])
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
        
        # Fetch course ID
        course_id = fetch_course_id(body['shortname'], url, token)
        print(f'Course ID: {course_id}')
        
        # Set shortname since we remove it from the dict
        shortname = body['shortname']
        
        # Set meeting id to None for log, in case of error
        meeting_id = 'None'
        
        # Check if course_id is int and change to string for error checking
        if isinstance(course_id, int):
            course_id = str(course_id)
            
        # Check for error and skip iteration if found
        if course_id[0: 5] != 'Error':
            # Remove the shortname field before creating a meeting
            del body['shortname']
            
            if body['schedule_for'] == 'tbd@pacificcollege.edu':
                print(f'{shortname} Teacher TBD')
            else:
                print(f'Creating Meeting: {body["topic"]}')
                # Create Meeting or TODO: Check if meeting exists and Update meeting

                meeting_id = new_meeting_request(new_jwt, body)
                print(f'Meeting ID: {meeting_id}')
            
                # Store meeting and course ID
                lti_csv = store_data(lti_csv, meeting_id, course_id)
        
        # Log created meeting, course ID, and shortname for reference if the meeting has been created
        log_csv = log_data(log_csv, meeting_id, course_id, shortname)
    
    if write_csv(lti_csv, f'mdl-zoom{time.time()}.csv'):
        print(f'File successfully created!')
    else:
        print(f'Error writting CSV file!')
        
    if write_log(log_csv, f'log{time.time()}.csv'):
        print(f'File successfully created!')
    else:
        print(f'Error writting log file!')