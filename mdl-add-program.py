import csv
import http.client
import json
import jwt
from datetime import datetime, timedelta
import time
from typing import NamedTuple, Dict, Union, cast
import smtplib
from email.message import EmailMessage
import argparse

API_KEY_KEY = 'api_key'
API_SECRET_KEY = 'api_secret'
TOKEN = 'token'
URL = 'url'
EMAIL_USER = 'email_user'
EMAIL_PASS = 'email_pass'

Creds = NamedTuple('Creds', [('key', str), ('secret', str), ('url', str), ('token', str), ('email_user', str), ('email_pass', str)])

# Open Schedule CSV
# ---Start---
def read_csv(filename: str):
    meetings = []
    with open(filename, newline='') as csvfile:
        meeting_reader = csv.reader(csvfile, dialect='excel', delimiter=',', quotechar='|')
        next(meeting_reader)
        for row in meeting_reader:
            meetings.append({
                'program_name': f'{row[0].rstrip()}',
                'short_name': f'{row[1].rstrip()}'
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
    email_user = raw_creds[EMAIL_USER]
    email_pass = raw_creds[EMAIL_PASS]
    
    return Creds(key, secret, url, token, email_user, email_pass)

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

# Update Course
# ---Start---
def update_course(course_id: str, program_name: str, url: str, token: str) -> str:
    course_id = cast(int, course_id)
    conn = http.client.HTTPSConnection(url)
    function = 'core_course_update_courses'
    body = {
                'courses': {
                   0: {
                        'id': course_id,
                        'customfields': {
                            0: {
                                'shortname': 'program',
                                'value': program_name
                            }
                        }
                    }
                }
            }
    print(json.dumps(body))
    # body = {
    #             'courses': [
    #                {
    #                     'id': course_id,
    #                     'customfields': [
    #                         {
    #                             'shortname': 'program',
    #                             'value': program_name
    #                         }
    #                     ]
    #                 }
    #             ]
    #         }
    try:
        conn.request('POST', f'/webservice/rest/server.php?wstoken={token}&wsfunction={function}&moodlewsrestformat=json&courses[0][id]={course_id}&courses[0][customfields][0][shortname]=program&courses[0][customfields][0][value]={program_name}', body=None, headers={})
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = { 
                'warnings': {
                    0: {
                        'item': course_id,
                        'warningcode': f'Error: {x} occured'
                    }
                }
               }
  
    return data
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
    parser = argparse.ArgumentParser(description='Backs up Zoom cloud recordings')
    parser.add_argument(
        '--file',
        metavar='CSV_FILE',
        required=True,
        help='CSV file of meeting settings'
    )
    
    args = parser.parse_args()
    
    # Create JWT
    key, secret, url, token, email_user, email_pass = read_credentails()
    new_jwt = generate_jwt(key, secret)

    # Read Schedule
    meetings = read_csv(args.file)
    
    # Create a list and log to write to CSV
    lti_csv = []
    log_csv = []
    
    # Loop through schedule
    for body in meetings:
        course_id = fetch_course_id(body["short_name"], url, token)
        
        # Check if course_id is int and change to string for error checking
        if isinstance(course_id, int):
            course_id = str(course_id)
            
        print(body['short_name'])
        print(course_id)
            
        if course_id[0: 5] == 'Error':
            continue
        
        update_response = update_course(course_id, body['program_name'], url, token)
        
        print('Response')
        print('--------')
        print(update_response)
        print('--------')
            

        