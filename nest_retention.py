#!/usr/bin/env python3.5

### LICENSE ###
# Nest Retention Project
# Created to save data from Nest into a CSV file.
# Copyright (C) 2017  - Geran Smith

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# If you have any issues, please post on the GitHub page for this project: <https://github.com/tehspaceg/NestRetentionProject>

# 'nest' for python-nest requirements, 'requests' for mailgun and OpenWeatherMap, 'csv' for writing out to csv format, 'sys' for base operations, 'argparse' for hanging the pin argument, 'os.path' for checking for existing files, 'datetime' and 'pytz' for getting current datetime in UTC format, 'json' for reading OpenWeatherMap data
import nest
import requests
import csv
import sys
import argparse
import os.path
import datetime
import pytz
import json

# Use credentials from the Nest API
client_id = 'xxxx'
client_secret = 'xxxx'
access_token_cache_file = 'nest.json'

#base mailgun information
mailgun_key = 'xxxxx' #replace with your mailgun key
mailgun_url = 'https://api.mailgun.net/v3/domain/messages' #replace with your base URL plus the messages object
mailgun_recipient = 'xxx@yyy.com' #replace with your target email
mailgun_from = 'zzz@ppp.com' #replace with the from address to use

# OpenWeatherMap API information
owm_key = 'xxx'
owm_cityid = 'xxx' # Get this from http://openweathermap.org/find, then get the City ID from the URL
owm_units = 'imperial' # Set to imperial for Fahrenheit, metric for Celsius

# Enter path to to the csv output file
csv_output = '/path/to/nest_retention/nest_retention_output.csv'

# Enter path to the test file
testfile = '/path/to/nest_retention/testfile'

# Exits if the test file exists, the goal being to not spam a bunch of APIs if the Nest PIN is needed
if os.path.isfile(testfile):
    print('The test file exists, exiting...')
    sys.exit()

# define the main function
def main(argv):
    # Handle arguments saying we need a pin
    parser = argparse.ArgumentParser(description='Pass an argument if a PIN is required')
    parser.add_argument('--pin', action='store_true', dest='pin', help='Set this flag if a PIN needs to be entered')
    args = parser.parse_args()
    
    # Create the csv file if needed
    if not os.path.isfile(csv_output):
        with open(csv_output,'w') as f:
            f.write('Date,Device Name,Device Location,Mode,HVAC State,Temperature,Target Temperature,Outside Temperature\n')
    
    # Get the current datetime in ISO format
    utc_now = pytz.utc.localize(datetime.datetime.utcnow())
    iso_utc_now = utc_now.isoformat()
    
    # Get the current weather information from OpenWeatherMap
    payload = {'id': owm_cityid, 'units': owm_units, 'appid': owm_key}
    openweathermap = requests.get('http://api.openweathermap.org/data/2.5/weather', params=payload)
    if openweathermap.status_code == requests.codes.ok:
        owm_decoded = openweathermap.json()
        owm_temperature = owm_decoded['main']['temp']
    else:
        bad_r.raise_for_status()
    
    # Authorize against the Nest API
    napi = nest.Nest(client_id=client_id, client_secret=client_secret, access_token_cache_file=access_token_cache_file)
    
    # Check to see if a pin is required by the Nest authentication, if it is required, look for the pin argument
    if napi.authorization_required:
    # If the pin argument was set, we want to wait and allow a pin to be entered manually
        if args.pin:
            print('Go to ' + napi.authorize_url + ' to authorize, then enter PIN below')
            if sys.version_info[0] < 3:
                pin = raw_input("PIN: ")
            else:
                pin = input("PIN: ")
            napi.request_token(pin)
        else:
            if sys.version_info[0] < 3:
                file = open(testfile, 'w')
                request = requests.post(mailgun_url, auth=('api', mailgun_key), data={
                'from': mailgun_from,
                'to': mailgun_recipient,
                'subject': 'Nest Retention Project PIN requested',
                'text': 'Created file to stop this script'})
            else:
                file = open(testfile, 'w')
                request = requests.post(mailgun_url, auth=('api', mailgun_key), data={
                'from': mailgun_from,
                'to': mailgun_recipient,
                'subject': 'Nest Retention Project PIN requested',
                'text': 'Created file to stop this script'})

    for structure in napi.structures:
        print ('Structure %s' % structure.name)
        print ('    Away: %s' % structure.away)
        print ('    Devices:')

        for device in structure.thermostats:
            print ('        Device: %s' % device.name)
            print ('            Temp: %0.1f' % device.temperature)

    # Access advanced structure properties:
    for structure in napi.structures:
        print ('Structure   : %s' % structure.name)
        print (' Postal Code                    : %s' % structure.postal_code)
        print (' Country                        : %s' % structure.country_code)
        print (' num_thermostats                : %s' % structure.num_thermostats)

    # Access advanced device properties:
        for device in structure.thermostats:
            print ('        Device: %s' % device.name)
            print ('        Where: %s' % device.where)
            print ('            Mode       : %s' % device.mode)
            print ('            HVAC State : %s' % device.hvac_state)
            print ('            Fan        : %s' % device.fan)
            print ('            Fan Timer  : %i' % device.fan_timer)
            print ('            Temp       : %0.1fC' % device.temperature)
            print ('            Humidity   : %0.1f%%' % device.humidity)
            print ('            Target     : %0.1fC' % device.target)
            print ('            Eco High   : %0.1fC' % device.eco_temperature.high)
            print ('            Eco Low    : %0.1fC' % device.eco_temperature.low)
            print ('            hvac_emer_heat_state  : %s' % device.is_using_emergency_heat)
            print ('            online                : %s' % device.online)
            
            # Write data to csv file
            with open(csv_output, 'a', newline='') as f:
                writer=csv.writer(f)
                writer.writerow([iso_utc_now, device.name, device.where, device.mode, device.hvac_state, device.temperature, device.target, owm_temperature    

try:
    if __name__ == "__main__":
        main(sys.argv[1:])

# exception handlers
except KeyboardInterrupt:
    sys.exit()
except Exception as e:
    request = requests.post(mailgun_url, auth=('api', mailgun_key), data={
    'from': mailgun_from,
    'to': mailgun_recipient,
    'subject': 'Nest Retention Project failed in the last try/catch',
    'text': str(e)})
    raise e
