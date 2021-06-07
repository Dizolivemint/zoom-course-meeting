import csv
import http.client
import json
import jwt
from datetime import datetime, timedelta
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
    try:
        with open(filename, newline='') as csvfile:
            meeting_reader = csv.reader(csvfile, dialect='excel', delimiter=',', quotechar='|')
            next(meeting_reader)
            for row in meeting_reader:
                meetings.append({
                    'id': f'{row[0].rstrip()}',
                    'course_id': f'{row[1].rstrip()}'
                })
    except:
        meetings = []
    return meetings
# ---End---

# Open Log CSV
# ---Start---
def read_log(log_name: str):
    meetings = []
    try:
        with open(log_name, newline='') as csvfile:
            meeting_reader = csv.reader(csvfile, dialect='excel', delimiter=',', quotechar='|')
            next(meeting_reader)
            for row in meeting_reader:
                meetings.append({
                    'course_name': f'{row[0].rstrip()}',
                    'course_id': f'{row[1].rstrip()}',
                    'meeting_time': f'{row[2].rstrip()}'
                })
    except:
        meetings = []
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
def log_data(log_csv: list, course_name: str, course_id: str, meeting_time: str) -> list:
    log_csv.append([
        course_name,
        course_id,
        meeting_time
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
        '--file',
        metavar='CSV_FILE',
        required=True,
        help='CSV file of meeting settings'
    )
    
    args = parser.parse_args()
    list_name = args.file
    log_name = 'log'
    
    # Create JWT
    key, secret, url, token, email_user, email_pass = read_credentails()
    new_jwt = generate_jwt(key, secret)

    # Read Schedule
    meetings = read_csv(list_name)
    
    # Read Log
    # Course ID and Meeting Time
    log = read_log(f'{log_name}.csv')
    
    # Create a list and log to write to CSV
    lti_csv = []
    log_csv = []
    
    # Loop through schedule
    for body in meetings:
        enrolled_user = []
        meeting_attendee = []
        skip_attendance = False
        
        # Get course name
        meeting = get_meeting_report(new_jwt, body)
        meeting_time = meeting['start_time']
        course_name = meeting['topic']

        # Get enrolled users from Moodle
        users = fetch_course_users(body['course_id'], url, token)
        
        print('______________________')
        print(course_name)
        print(f'Course ID: {body["course_id"]}')
        print('______________________')
        
        course_data = fetch_course(body['course_id'], url, token)
        course_program = course_data[0]['customfields'][0]['value']
        print('Course Program')
        print('-----------')
        print(course_program)
        print('-----------')
        
        mdl_uid = 0
        mdl_user = []
        for user in users:
            print(f'Enrolled User: {user["email"]}')
            print(f'Enrolled User First Name: {user["firstname"]}')
            print(f'Enrolled User Last Name: {user["lastname"]}')
            enrolled_user.append(user["email"])
            mdl_user.append({ "id": mdl_uid, "email": user["email"], "firstname": user["firstname"], "lastname": user["lastname"] })
            mdl_uid += 1
        
        
        # Get participants from Zoom Meeting
        participants = get_meeting_participants_report_request(new_jwt, body)
        for participant in participants:
            # print(participant)
            print(f'Meeting Participant: {participant["user_email"]}')
            # print(f'join_time: {participant["join_time"]}')
            # print(f'leave_time: {participant["leave_time"]}')
            meeting_attendee.append(participant["user_email"])
            
        # Compare emails and log students that did not attend
        filtered = [email for email in enrolled_user if email not in meeting_attendee]
        print(f'Absent: {filtered}')
        absentees = []
        for email in filtered:
            # print('Absentee values:')
            # print(enrolled_user.index(email))
            # print(mdl_user[enrolled_user.index(email)])
            absentees.append(mdl_user[enrolled_user.index(email)])
            
        # Skip logic
        in_log = [instance for instance in log if instance['course_id'] == body['course_id']]
        if len(in_log) > 0:
            print(in_log)
            if in_log[0]['meeting_time'] == meeting_time:
                skip_attendance = True
        if (len(enrolled_user) / len(meeting_attendee)) > 2 :
            skip_attendance = True
        if len(filtered) < 1:
            skip_attendance = True
        
        # Send attendance if no skip
        if skip_attendance == False:
            # continue
            send_attendance(absentees, course_name, body["course_id"], course_program, meeting_time, email_user, email_pass)
        
            # Log result
            log_csv = log_data(log_csv, course_name, body["course_id"], meeting_time)
            
            if write_log(log_csv, f'{log_name}.csv'):
                print(f'Logged to file!')
            else:
                print(f'Error writting log file!')
        else:
            print('---==== Skipped ====---')
    print('Finished processing attendance!')