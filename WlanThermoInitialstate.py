import os
import urllib2
import json
import glob
import time
from ISStreamer.Streamer import Streamer

# --------- User Settings ---------
BUCKET_NAME = "xxxxxxxxx"
BUCKET_KEY = "xxxxxxxx"
ACCESS_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxx"

# ---------- depencies -----------------------
# run the following command to aktivate ISStreamer for Inital State:
# \curl -sSL https://get.initialstate.com/python -o - | sudo bash
# at console

# run cyclic as cron job
# crontab -e
# ad:
# * * * * * /usr/bin/python ./WlanThermoInitialstate.py
#                           ad your path here

# ---------- getting Data -----------------------
def get_values():
    api_conditions_url = "http://localhost/app.php"
    try:
        f = urllib2.urlopen(api_conditions_url)
    except:
        print "Failed to get conditions"
        return []
    json_conditions = f.read()
    f.close()
    return json.loads(json_conditions)

def main():
    # -------------- WlanThermo --------------
    values = get_values()
    if ('temp_unit' not in values):
        print "Error! Wlanthermo app.php reading failed!"
        exit()
    else:
        # init ISStreamer
        streamer = Streamer(bucket_name=BUCKET_NAME, bucket_key=BUCKET_KEY, access_key=ACCESS_KEY)

        # Calculate Values
        if values['temp_unit'] == 'celsius':
           unit = "C"
        else:
           unit = "F"
   
        # Stream valid values to Initial State
        streamer.log("temp_unit", unit)
        streamer.log("cpu_load", round(values['cpu_load'],2))
        streamer.log("cpu_temp", values['cpu_temp'])
       
        # Stream Channel-data
        for x in values['channel']:
            channel = values['channel'][x]
            if channel['state'] == 'ok' and channel['show']:
                temp = channel['temp']
                temp_min = channel['temp_min']
                temp_max = channel['temp_max']
                streamer.log("Ch_"  + x + '_Name', channel['name'])
                streamer.log("Ch_"  + x + '_Temp', temp )
                streamer.log("Ch_"  + x + '_Min', temp_min )
                streamer.log("Ch_"  + x + '_Max', temp_max )
                #add channel datapoints here
               
        # Stream PitMaster 1
        if values['pit']['enabled']:
            streamer.log("Pit1_setpoint", values['pit']['setpoint'])
            streamer.log("Pit1_current", values['pit']['current'])
            streamer.log("Pit1_control_out", values['pit']['control_out'])
            streamer.log("Pit1_Last", values['pit']['timestamp'])
           
        # Stream PitMaster 2
        if ('pit2' in values):
            if values['pit2']['enabled']:
                streamer.log("Pit2_setpoint", values['pit2']['setpoint'])
                streamer.log("Pit2_current", values['pit2']['current'])
                streamer.log("Pit2_control_out", values['pit2']['control_out'])
                streamer.log("Pit2_Last", values['pit2']['timestamp'])
       
        #add other datapoints here

        streamer.flush()

if __name__ == "__main__":
    main()
