import time
import datetime
import pickle
from os import path
from collections import namedtuple
from hashlib import sha3_256
from datetime import datetime, timedelta

import requests
import pytz
from bs4 import BeautifulSoup

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient import errors



Event = namedtuple('Event', 'date location speaker institute title links id')


def get_seminars():
    """Yields 'Event' objects containing info from the 'campusmatrinsried.de' site."""
    r = requests.get('https://campusmartinsried.de/en/seminars/')
    if r.status_code != 200:
        raise IOError

    events = BeautifulSoup(r.text, features="html.parser").find_all('article')
    for event in events:
        date = datetime.strptime(event.find(attrs='datetime').text.strip(), '%d.%m.%Y %H:%M')  # 18.02.2019, 13:00
        speaker, institute, title = list(event.find(attrs={'class': 'speaker-title'}).stripped_strings)
        links = [a.get('href') for a in event.find_all('a')]
        location = ', '.join(event.find(attrs={'class': 'location-col'}).stripped_strings)
        hasher = sha3_256()
        hasher.update(title.encode())
        id = hasher.hexdigest()
        yield Event(date=date, speaker=speaker, institute=institute, title=title, location=location, links=links, id=id)


def get_valid_google_service(credentials_path, credentials_filename='credentials.json', token_filename='token.pickle', scopes=['https://www.googleapis.com/auth/calendar']):
    """
    Connect to Google's servers, using either the either the credentials file token file found in 'credentials_path'.

    Args:
        - credentials_path: The directory where the credentials.json and token.json files can be found.
        - credentials_filename: The filename of the json file from Google with all the login info.
        - token_filename: the pickle filename that stores the user's access and refresh tokens.
                It is created automatically when the authorization flow completes for the first time.


    """

    credentials_file = path.join(credentials_path, credentials_filename)
    token_file = path.join(credentials_path, token_filename)
    credentials = None
    # The file token.pickle
    if path.exists(path.join(credentials_path, token_file)):
        with open(path.join(credentials_path, token_file), 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            credentials = flow.run_local_server()
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)

    service = build('calendar', 'v3', credentials=credentials)
    return service


def create_google_event(event, timezone='Europe/Berlin'):
    """Returns a Google Calendar-compatible dictionary from an 'Event' object."""

    dst_offset = pytz.timezone(timezone).localize(event.date).strftime('%z')
    dst_offset = "{}:{}".format(dst_offset[:3], dst_offset[3:])  # format dst as "+HH:MM" for google calendar.

    google_event = {
        'id': event.id,
        'summary': '{} ({})'.format(event.title, event.speaker),
        'location': event.location,
        'description': '{}\n{}'.format(event.institute, event.links),
        'start': {
            'dateTime': event.date.strftime('%Y-%m-%dT%H:%M:00{}'.format(dst_offset)),  # '2018-02-20T17:00:00+01:00'
            'timeZone': 'Europe/Berlin',
        },
        'end': {
            'dateTime': (event.date + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:00{}'.format(dst_offset)),
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
    return google_event


def main(calendar_id, credentials_path):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    service = get_valid_google_service(credentials_path=credentials_path)
    for seminar in get_seminars():
        try:
            service.events().get(calendarId=calendar_id, eventId=seminar.id).execute()  # try to get event, to see if it already exists
        except errors.HttpError:  # event doesn't exist yet.
            event = create_google_event(event=seminar)
            inserted_event = service.events().insert(calendarId=calendar_id, body=event).execute()
            print('event created: {}'.format(inserted_event.get('htmlLink')))


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='Campus Martinsried Semionars Calendar Exporter.')
    parser.add_argument('--credentials_path', default=r'C:\Users\delgrosso\PycharmProjects\mpi_calendar',
                        help='The directory where the crediental files are found.')
    parser.add_argument('--calendar_id', default='osic1vum93es6r8cnms31rmh2o@group.calendar.google.com',
                        help='The google calendar id to export to.')

    args = parser.parse_args()

    try:
        main(credentials_path=args.credentials_path, calendar_id=args.calendar_id)
    except Exception as e:
        print(e)
        time.sleep(10)