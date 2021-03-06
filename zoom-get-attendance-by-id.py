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

# Get Meeting
# ---Start--- #
def get_meeting(valid_jwt: str, meeting: dict) -> str:
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
        data = { 'topic': f'Error: {x} occured on call to fetch user' }
        return cast(str, data['topic'])

    # Error check if there is an issue finding the user
    if 'code' in data:
        data = { 'topic': f'Error: {data["message"]} occured on call to get meeting' }

    return data
# ---End---

# Get Meeting Report
# ---Start--- #
def get_meeting_report(valid_jwt: str, meeting: dict) -> str:
    data = {}
    conn = http.client.HTTPSConnection('api.zoom.us')
    headers = {
		'authorization': f'Bearer {valid_jwt}',
		'content-type': 'application/json'
	}
    try:
        conn.request('GET', f'/v2/report/meetings/{meeting["id"]}', body=None, headers=headers)
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = { 'topic': f'Error: {x} occured on call to fetch user' }
        return cast(str, data['topic'])

    # Error check if there is an issue finding the user
    if 'code' in data:
        data = { 'topic': f'Error: {data["message"]} occured on call to get meeting' }

    return data
# ---End---

# Get Meeting Participants
# ---Start--- #
def get_meeting_participants_report_request(valid_jwt: str, meeting_id: dict) -> str:
    data = {}
    conn = http.client.HTTPSConnection('api.zoom.us')
    headers = {
		'authorization': f'Bearer {valid_jwt}',
		'content-type': 'application/json'
	}
    print('________________________')
    print('Meeting: ' + meeting_id)
    try:
        conn.request('GET', f'/v2/report/meetings/{meeting_id}/participants?page_size=300', body=None, headers=headers)
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = { 'participants': f'Error: {x} occured on call to fetch user' }
        return cast(str, data['participants'])

    # Error check if there is an issue finding the user
    if 'code' in data:
        data = { 'participants': f'Error: {data["message"]} occured on call to get participants' }

    # print('Participants response')
    # print(data)
    return cast(str, data['participants'])
# ---End---


# Fetch Course
# ---Start---
def fetch_course(course_id: str, url: str, token: str) -> str:
    conn = http.client.HTTPSConnection(url)
    function = 'core_course_get_courses'
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
    return data
# ---End---

# Fetch Course Users
# ---Start---
def fetch_course_users(course_id: str, url: str, token: str) -> str:
    conn = http.client.HTTPSConnection(url)
    function = 'core_enrol_get_enrolled_users'
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

# Append CSV for Zoom LTI (Meeting ID and Moodle Course ID)
# ---Start---
def write_log(log_csv: list, out_filename: str) -> bool:
    with open(out_filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for log in log_csv:
            writer.writerow(log)
    
    csvfile.close()
    
    return True
# ---End---

# Create and send email for the meeting
def send_attendance(absentees: list, course_name: str, course_id: str, course_program: str, meeting_time: str, email_user: str, email_pass: str):
    course_campus = 'San Diego'
    if course_name.find('.NY') != -1:
        course_campus = 'New York'
    if course_name.find('.CH') != -1:
        course_campus = 'Chicago'
    
    for user in absentees:
        msg = EmailMessage()
        msg.set_content(f'''Synchronous Course Student Attendance
        First Name: {user["firstname"]}
        Last Name:  {user["lastname"]}
        Email: {user["email"]}
        Course Name:  {course_name}
        Course Link: https://elearning.pacificcollege.edu/course/view.php?id={course_id}
        Reason: Did not attend Zoom class meeting
        Meeting date/time: {meeting_time}
        {course_campus}
        {course_program}''')
        msg['Subject'] = 'Synchronous Course Student Attendance'
        msg['From'] = 'eLearning <elearning@pacificcollege.edu>'
        msg['To'] = 'mexner@pacificcollege.edu'
        # Send email
        mailserver = smtplib.SMTP('smtp.office365.com',587)
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(email_user, email_pass)
        #Adding a newline before the body text fixes the missing message body
        mailserver.send_message(msg)
        mailserver.quit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backs up Zoom cloud recordings')
    parser.add_argument(
        '--id',
        metavar='MEETING_ID',
        required=True,
        help='Enter a meeting ID'
    )
    
    args = parser.parse_args()
    
    # Create JWT
    key, secret, url, token, email_user, email_pass = read_credentails()
    new_jwt = generate_jwt(key, secret)

    # Read Schedule
    meeting_id = args.id
    
    # Create a list and log to write to CSV
    lti_csv = []
    log_csv = []
    

      
    # Get participants from Zoom Meeting
    participants = get_meeting_participants_report_request(new_jwt, meeting_id)
    
    print('Participants')
    print('_____________')
    print(participants)
        
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