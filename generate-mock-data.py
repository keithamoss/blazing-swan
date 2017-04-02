import glob
import datetime as dt
import numpy as np
import pandas as pd
import sqlite3

# http://stackoverflow.com/questions/1883980/find-the-nth-occurrence-of-substring-in-a-string
def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

def fixtimestamp(timestamp):
    # Pad month with 0
    if timestamp[1] == "/":
        timestamp = "0" + timestamp
    
    # Pad day with 0
    if timestamp[4] == "/":
        timestamp = timestamp.replace(timestamp[0:3], timestamp[0:3] + "0")
    
    ## From January 2015 onwards ONLY
    # WTF - Hours are single digits (" 0:01")
    if len(timestamp[timestamp.find(" "):]) == 5:
        timestamp = timestamp.replace(timestamp[timestamp.find(" ") + 1:], "0" + timestamp[timestamp.find(" ") + 1:] + ":00")

    # WTF - Hours are double digits (" 10:00")
    if len(timestamp[timestamp.find(" "):]) == 6:
        timestamp = timestamp.replace(timestamp[timestamp.find(" ") + 1:], timestamp[timestamp.find(" ") + 1:] + ":00")

    return timestamp

# SELECT bikeid, COUNT(*) FROM bikes GROUP BY bikeid ORDER BY COUNT(*) DESC
conn = sqlite3.connect("bikes-all-years.db")

# for fname in glob.glob("./data/citibikenyc/*.csv"):
#     print(fname)
#     bikes = pd.read_csv(fname)

#     ## The casing in the column names changed in October 2016
#     # Pre-October 2016
#     # bikes = bikes[['bikeid', 'starttime', 'start station latitude', 'start station longitude']]
#     # bikes.rename(columns={'starttime': 'timestamp', 'start station latitude': 'lat', 'start station longitude': 'lon'}, inplace=True)

#     bikes = bikes[['Bike ID', 'Start Time', 'Start Station Latitude', 'Start Station Longitude']]
#     bikes.rename(columns={'Bike ID': 'bikeid', 'Start Time': 'timestamp', 'Start Station Latitude': 'lat', 'Start Station Longitude': 'lon'}, inplace=True)

#     bikes = bikes.assign(voltage=np.nan)

#     ## The date format changed from 2013-07-01 00:00:02 to 9/1/2014 00:00:25 in September 2014
    
#     # Post-September 2014
#     # bikes['timestamp'] = bikes['timestamp'].map(fixtimestamp)

#     # Pre-September 2014 and Post-September 2016
#     bikes['timestamp'] = pd.to_datetime(bikes['timestamp'], format="%Y-%m-%d %H:%M:%S")

#     # Post-September 2014
#     # bikes['timestamp'] = pd.to_datetime(bikes['timestamp'], format="%m/%d/%Y %H:%M:%S")

#     bikes['timestamp'] = (bikes['timestamp'] - dt.datetime(1970,1,1)).dt.total_seconds()

#     bikes = bikes.set_index(['bikeid', 'timestamp'])
#     bikes.to_sql("bikes", conn, if_exists="append")



# topbikes = pd.read_sql_query("SELECT * FROM bikes WHERE bikeid IN (SELECT bikeid FROM bikes GROUP BY bikeid ORDER BY COUNT(*) DESC LIMIT 5);", conn)

# topbikes = topbikes.set_index(['bikeid', 'timestamp'])
# topbikes.to_sql("topbikes", conn, if_exists="replace")