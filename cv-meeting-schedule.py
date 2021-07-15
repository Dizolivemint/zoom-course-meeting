import csv
import http.client
import json
import jwt
from datetime import datetime, timedelta
import time
from typing import NamedTuple, Dict, Union, cast

API_KEY_KEY = 'c_api'

# Read and process credentials
# ---Start---
def read_credentials() -> str:
    raw_creds: Dict[str, str] = {}
    with open('zoom_creds', 'r') as cred_file:
        for line in cred_file.readlines():
            (key, value) = line.strip().split('=')
            raw_creds[key] = value

    key = raw_creds[API_KEY_KEY]
    
    return key

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
def get_courses(campusId: int, termId: int) -> str:
    data = {}
    conn = http.client.HTTPSConnection('sisclientweb-100299.campusnexus.cloud')
    key = read_credentials()
    headers = {
		'ApiKey': f'{key}',
		'Content-Type': 'application/json',
        'Accept': 'application/json'
	}
    try:
        conn.request('GET', f'/ds/campusnexus/ClassSections/CampusNexus.GetBatchRegistrationClassSections(campusId={campusId},termId={termId})', body=None, headers=headers)
        res = conn.getresponse()
        data = json_to_dict(res)
    except Exception as x:
        data = { 'value': f'Error: {x} occured on call to fetch courses' }
        return cast(str, data['value'])

    return cast(str, data['value'])
# ---End---

if __name__ == '__main__':
    print(f'Course data {get_courses(7, 57)}')