from pyspatialite import dbapi2 as db
from subprocess import call
import os
import random
import time

# CONFIG START
sleepTime = 3 # seconds - time to sleep after generating a map image
# CONFIG END

sqlite_path = "./data/bikes.sqlite"

if not os.path.isfile(sqlite_path):
    print "Error: Database %s doesn't exist." % (sqlite_path)

else:
    # Connect
    # conn = db.connect(sqlite_path)
    # cur = conn.cursor()

    while True:
        if os.path.isfile("./bikes.tmp.png"):
            os.remove("./bikes.tmp.png")
        
        with open("./bikes.tmp.png", "w+") as f:
            call(["mapserv", "-nh", "QUERY_STRING=map=./bikes.map&mode=map"], stdout=f)

        # http://stackoverflow.com/questions/2333872/atomic-writing-to-file-with-python
        # tl;dr This doens't work on Windows or across different file systems.
        # If running on Windows we can't guarnatee atomic renaming, so comment this line (which throws an error) 
        # and uncomment the lines directly below.
        os.rename("./bikes.tmp.png", "./bikes.png")

        # For Windows ONLY
        # if os.path.isfile("./bikes.png"):
        #     os.remove("./bikes.png")
        # os.rename("./bikes.tmp.png", "./bikes.png")

        print "Map generated."
        time.sleep(sleepTime)
    
    # conn.close()