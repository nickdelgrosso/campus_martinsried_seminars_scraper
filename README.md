# Martinsried Campus Seminars Scraper + Exporter

This is a small Python 3 script I wrote to make a Google calendar with the seminars available on-campus.  
It reads the seminar event list from the table on the campusmartinsried.de web page and exports them to Google Calendar.
This script is run periodically to keep the list up-to-date. 

## Installation

First, download the code and install the python package dependencies:
```bash
git clone https://github.com/nickdelgrosso/campus_martinsried_seminars_scraper
cd campus_martinsried_seminars_scraper
pip install -r requirements.txt

```  

## Run

  - you need a 'credentials.json' file from Google to get permission to connect to their API.  
See their tutorial's "Step 1" to do this: https://developers.google.com/calendar/quickstart/python, and save the 'credentials.json' file on your computer.   

  - Create a Google calendar and note the calendar's ID.  (It will look something like: ogic1tum92es6r3cnms31lmh2o@group.calendar.google.com)
  
  - Run the 'register_event.py' script, giving the directory where the credentials file is stored and the calendar id.
  
```bash
python register_event.py --credentials_path C:\CredentialsPath  --calendar_id  ogic1tum92es6r3cnms31lmh2o@group.calendar.google.com
``` 

That's it!  At the moment, I use Windows Task Schedular to run this script once a day, but in the future other strategies can be used.


## Acknowledgments

Thanks to the campusmartinsried.de team for compiling and providing the seminar information to the whole Martinsried area! 

## Future Features

This script is certainly not feature-complete.  These features are not currently present in the code:

  - Auto-Deletion of cancelled events.
  - Detection of modified events
  - Local event storage (currently, the script queues Google for every single event to see if it exists already before submitting.)
  