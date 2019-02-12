from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient import errors

from collections import namedtuple
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from hashlib import md5


Event = namedtuple('Event', 'date location speaker institute title links id')

calendarId = 'oc42qfr79m6k6g1ttflgl1b36g@group.calendar.google.com'

def get_seminars():
    r = requests.get('https://campusmartinsried.de/en/seminars/')
    if r.status_code != 200:
        raise IOError

    events = BeautifulSoup(r.text, features="html.parser").find_all('article')
    for event in events:
        date = datetime.strptime(event.find(attrs='datetime').text.strip(), '%d.%m.%Y %H:%M')  # 18.02.2019, 13:00
        speaker, institute, title = list(event.find(attrs={'class': 'speaker-title'}).stripped_strings)
        links = [a.get('href') for a in event.find_all('a')]
        location = ', '.join(event.find(attrs={'class': 'location-col'}).stripped_strings)
        hasher = md5()
        hasher.update(title.encode())
        id = hasher.hexdigest()
        yield Event(date=date, speaker=speaker, institute=institute, title=title, location=location, links=links, id=id)


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)



    for seminar in get_seminars():

        try:
            service.events().get(calendarId=calendarId, eventId=seminar.id).execute()  # try to get event, to see if it already exists
        except errors.HttpError:  # event doesn't exist yet.

            event = {
                'id': seminar.id,
                'summary': '{} ({})'.format(seminar.title, seminar.speaker),
                'location': seminar.location,
                'description': '{}\n{}'.format(seminar.institute, seminar.links),
                'start': {
                    'dateTime': seminar.date.strftime('%Y-%m-%dT%H:%M:00+01:00'), #  '2018-02-20T17:00:00+01:00'
                    'timeZone': 'Europe/Berlin',
                },
                'end': {
                    'dateTime': (seminar.date + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:00+01:00'),
                    'timeZone': 'Europe/Berlin',
                },
                'recurrence': [
                ],
                'attendees': [
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [],
                },
            }
            event = service.events().insert(calendarId=calendarId, body=event).execute()
            print('event created: {}'.format(event.get('htmlLink')))


if __name__ == '__main__':
    main()