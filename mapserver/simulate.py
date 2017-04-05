from pyspatialite import dbapi2 as db
import os
import random
import time

# CONFIG START
featuresToCreate = 500 # Features to create per bike
sleepTime = 0 # seconds - set to 0 to disable sleeping between inserting each point
timestampRangeStart = 538613889
timestampRangeEnd = timestampRangeStart + (60 * 60 * 24 * 5)
bikeIdMin = 1
bikeIdMax = 5
# CONFIG END

sqlite_path = "./data/bikes.sqlite"

if not os.path.isfile(sqlite_path):
    print "Error: Database %s doesn't exist." % (sqlite_path)

else:
    # Connect
    conn = db.connect(sqlite_path)
    cur = conn.cursor()

    # Generate a collection of random points for each bike from which we'll make continuous lines
    points = {}
    for bikeid in range(bikeIdMin, bikeIdMax + 1):
        points[bikeid] = []
        for i in range(0, featuresToCreate):
            lat = random.uniform(117.5, 118.8)
            lon = random.uniform(-32, -33.5)
            points[bikeid].append({"lat": lat, "lon": lon})

    # Create a new feature every n seconds
    for bikeid in points:
        print "BikeId %s" % (bikeid)
        for i, point in enumerate(points[bikeid][:-1]): # The last point forms the end of the second last line
            nextpoint = points[bikeid][i+1]
            timestamp = random.randrange(timestampRangeStart, timestampRangeEnd)

            sql = "INSERT INTO bikes (bikeid, timestamp, geom) VALUES (%d, %d, GeomFromText('LINESTRING(%f %f, %f %f)', 4326))" % (bikeid, timestamp, point["lat"], point["lon"], nextpoint["lat"], nextpoint["lon"])
            print sql

            cur.execute(sql)

            if sleepTime > 0:
                conn.commit()
                time.sleep(sleepTime)
        print
    
    if sleepTime == 0:
        conn.commit()
    conn.close()

    print "Table `bikes` populated with %s new records." % (featuresToCreate)