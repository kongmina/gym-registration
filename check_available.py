#!/usr/bin/env python

import time
from typing import Any, Optional
from bs4 import BeautifulSoup
import requests
import pdb

_DEFINED_TIMES = ['6:00 PM-7:00 PM', '6:30 PM-7:30 PM', '7:00 PM-8:00 PM']
# _DEFINED_TIMES = ['11:00 AM-12:00 PM', '11:30 AM-12:30 PM']
_LOGIN_URL = 'https://www.inchargelife.com/App/NewMobileLogin.aspx'
_BOOKING_URL = 'https://www.inchargelife.com/App/Mobile/assets/tpl/pages/BookAccessControlAppointment.aspx'
_DEFINED_DAYS = ['Sunday', 'Tuesday', 'Wednesday', 'Thursday', 'Saturday']
_TARGET_DATE = '2020 July 31 Friday'

def day_in_target_days(day) -> bool:
    day_of_week = day.split(' ')[-1]
    return day_of_week in _DEFINED_DAYS

def get_payload_data(soup, ddl_day, button_id: Optional[Any] = None): 
    data = {
        '__SCROLLPOSITIONX': 0,
        '__SCROLLPOSITIONY': 0,
        }
    data['ddlLocation'] = soup.find(id="ddlLocation").option['value']
    data['ddlDays'] = ddl_day
    data['__EVENTVALIDATION'] = soup.find(id="__EVENTVALIDATION")['value']
    data['__VIEWSTATEGENERATOR'] = soup.find(id="__VIEWSTATEGENERATOR")['value']
    data['__VIEWSTATE'] = soup.find(id="__VIEWSTATE")['value']
    if button_id:
        data[button_id] = 'Book'
    return data

def is_target_time(time_text) -> bool:
    return time_text.split('\xa0')[0] in _DEFINED_TIMES
    
def has_remaining_spots(time_text) -> bool:
    return 'Spots Remaining: 0' not in time_text

def get_old_button_id(bookings):
    for booking in bookings:
        if booking.find(class_="btn-cancel"):
            return booking.find(class_="btn-cancel")['id']

def check_booking_page(soup: BeautifulSoup, ddl_day):
    total_bookings_available = int(soup.find(id='totalBookings').text)
    if total_bookings_available == 0:
        print("I don't have enough bookings to book a slot but I'll unbook when a time becomes available")
    while True:
        data_for_refresh = get_payload_data(soup, ddl_day)
        bookings = soup.findAll('tr')
        for i, booking in enumerate(bookings[1:]):
            try:
                text = booking.td.text
            except:
                continue
            old_button_id = ''
            if booking.find(class_="btn-cancel"):
                old_button_id = booking.find(class_="btn-cancel")['id']
            if is_target_time(text):
                if has_remaining_spots(text):
                    print(f"THERE'S AN OPEN SPOT ON {ddl_day} at the time i want!!")
                    #unbook old
                    if total_bookings_available == 0:
                        prev_button_id = old_button_id or get_old_button_id(bookings)
                        old_data = get_payload_data(soup, ddl_day, prev_button_id)
                        session_requests.post(_BOOKING_URL, data=old_data)
                    #book new
                    new_button_id = booking.find(class_="aspNetDisabled btn-insufficient")['id']
                    new_data = get_payload_data(soup, ddl_day, new_button_id)
                    session_requests.post(_BOOKING_URL, data=new_data)
                    print("new session booked")
                    exit()
        print("No available times found. Refreshing in 20 seconds")
        time.sleep(20)
        refreshed_page = session_requests.post(_BOOKING_URL, data=data_for_refresh).text
        refreshed_soup = BeautifulSoup(refreshed_page, 'lxml')
        soup = refreshed_soup

        # data = get_payload_data(soup, ddl_day)
        # temp_soup = session_requests.post(_BOOKING_URL, data).text
        # temp_soup = BeautifulSoup(temp_soup, 'lxml')
        # total_bookings_available = int(temp_soup.find(id='totalBookings').text)
            
        
    return False

session_requests = requests.session()
result = session_requests.get(_LOGIN_URL)
tree = BeautifulSoup(result.text, 'lxml')
viewstate_value = tree.find(id="__VIEWSTATE").get('value')
viewstate_generator_value = tree.find(id="__VIEWSTATEGENERATOR").get('value')
eventvalidation_value = tree.find(id="__EVENTVALIDATION").get('value')

payload = {
	"txtUsername": "Minakong", 
	"txtPassword": "honeypot", 
    "__VIEWSTATE": viewstate_value,
    "__VIEWSTATEGENERATOR": viewstate_generator_value,
    "__EVENTVALIDATION": eventvalidation_value,
    "btnLogin": "Login" 
}
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36",
    "Referer":_LOGIN_URL,
    "Connection": 'keep-alive',
    "Cookie":"ASP.NET_SessionId=yq5jsgtjfdbitlnew5cnmgims"
    }
result = session_requests.post(
	_LOGIN_URL, 
	data=payload,
)

html_file = session_requests.get(_BOOKING_URL, headers = dict(referer=_BOOKING_URL)).text  
soup = BeautifulSoup(html_file, 'lxml')
if soup.find('title').text != 'Book a Workout':
    print("Error logging in")
    exit()

while True: 
    _CURRENT_DATE = soup.find(id='ddlDays').text.split('\n')[1]
    dates = soup.find(id='ddlDays').text.split('\n')
    date = _TARGET_DATE
    # for date in dates:
    #     if date > _CURRENT_DATE and day_in_target_days(date) and len(target_dates) < 3:
    #         target_dates.append((date))

    # for date in target_dates:
    data = get_payload_data(soup, date)
    post_next_date = session_requests.post(_BOOKING_URL, data).text
    post_next_date_soup = BeautifulSoup(post_next_date, 'lxml')
    print(f"checking {date}")
    if check_booking_page(post_next_date_soup, date):
        print(f"Booked session on {date}")
    else:
        print(f"No sessions available on {date}")

