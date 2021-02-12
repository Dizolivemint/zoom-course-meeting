import csv
import requests
import json

# Open Schedule CSV
# ---Start---
with open('schedule.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile, dialect='excel', delimiter=',', quotechar='|')
    for row in spamreader:
        # print(', '.join(row))
        for col in row:
            print(col.rstrip())
# ---End---

# Create or Update Meeting
# ---Start--- #
# Request to see if meeting exists
# If !exists then Create Meeting
# Else Update Meeting
# ---End---

# Create Meeting
# ---Start---
# Create Meeting
# Fetch Course ID
# Store Meeting ID and Course ID
# ---End---

# Update Meeting
# ---Start---
# ---End---


# Fetch Course ID
# ---Start---
params = {
    'courseCode': courseCode
}

endpoint = 'https://el.edu'

result = requests.get(
    endpoint,
    headers=headers,
    params=params
)

output = result.json()

print(output['courseID'])
# ---End----

# Store Meeting ID and Course ID
# ---Start---
lti_csv = []
lti_csv.append({
    'meeting_id': meeting_id,
    'course_id': course_id,
    'meeting_url': meeting_url
})
# ---End---

# Write CSV for Zoom LTI (Meeting ID and Moodle Course ID)
# ---Start---
with open(out_filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Meeting ID', 'Course ID'])
# ---End---