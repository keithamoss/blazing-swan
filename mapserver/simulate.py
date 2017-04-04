from pyspatialite import dbapi2 as db
import os
import random
import time

# CONFIG START
featuresToCreate = 5 # Per run of the script
sleepTime = 1 # seconds
timestampRangeStart = 1491296400 # Tuesday April 4th 17:00
timestampRangeEnd = 1491555600 # Friday April 7th 17:00
# CONFIG END

sqlite_path = "./data/bikes.sqlite"

if not os.path.isfile(sqlite_path):
    print "Error: Database %s doesn't exist." % (sqlite_path)

else:
    # Connect
    conn = db.connect(sqlite_path)
    cur = conn.cursor()

    # Create a new feature every n seconds
    for i in range(0, featuresToCreate):
        bikeid = random.randrange(1, 6) # Actually 1 - 5 because Reasons
        lat = random.uniform(115, 117)
        lon = random.uniform(-32, -34)
        timestamp = random.randrange(timestampRangeStart, timestampRangeEnd)

        sql = "INSERT INTO bikes (bikeid, timestamp, geom) VALUES (%d, %d, GeomFromText('POINT(%f %f)', 4326))" % (bikeid, timestamp, lat, lon)
        print sql

        cur.execute(sql)
        conn.commit()

        time.sleep(sleepTime)
    
    conn.close()
    print "Table `bikes` populated with %s new records." % (featuresToCreate)