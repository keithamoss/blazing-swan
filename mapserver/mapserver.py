from pyspatialite import dbapi2 as db
from subprocess import call
from shutil import copyfile
import os
import random
import time

# CONFIG START
sleepTime = 3 # seconds - time to sleep after generating a map image
snapshotInterval = 10 # minutes - how often snapshots are saved to ./snapshots
# CONFIG END

sqlitePath = "./data/bikes.sqlite"
snapshotCounter = 0

if not os.path.isfile(sqlitePath):
    print "Error: Database %s doesn't exist." % (sqlitePath)

else:
    # Connect
    # conn = db.connect(sqlitePath)
    # cur = conn.cursor()

    while True:
        snapshotCounter += 1

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

        if (snapshotCounter * sleepTime) >= (snapshotInterval * 60):
            print "Snapshot!"
            snapshotCounter = 0

            copyfile("./bikes.png", "./snapshots/map-%s.png" % (time.strftime("%Y-%m-%d-%H-%M-%S")))

            if os.path.isfile("./snapshots/map-latest.png"):
                os.remove("./snapshots/map-latest.png")
            copyfile("./bikes.png", "./snapshots/map-latest.png")
        else:
            print "Snapshot pending! (%s vs %s)" % ((snapshotCounter * sleepTime), (snapshotInterval * 60))

        print "Map generated."
        time.sleep(sleepTime)
    
    # conn.close()