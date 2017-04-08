from pyspatialite import dbapi2 as db
from subprocess import check_output
from shutil import copyfile
import os
import random
import time
from datetime import datetime, timedelta
import imghdr
import sys

# CONFIG START
sleepTime = 0 # seconds - time to sleep after generating a map image
snapshotInterval = 0.2 # minutes - how often snapshots are saved to ./snapshots

#
# We have three different viz options
# Set noSteps = True to have all trails at 70% opacity.

# Set onlyTwoSteps = True and noSteps = False to have all trails from the last `latestTrailsThresholdHours` hours at 70% opacity, and all older trails at 50% opacity.

# Set noSteps = False and onlyTwoSteps = False to have all trails from the last `latestTrailsThresholdHours` hours at 70% opacity, and then a gradual reduction in opacity for `fadingTrailsSteps` steps according to the range given by `opacityStepMin` and `opacityStepMax`.
#
noSteps = False
onlyTwoSteps = False

latestTrailsThresholdHours = 3 # Number of hours for trails to appear at 70% opacity

# Trails older than `latestTrailsThresholdHours` hours will fade away according to the number of steps and opacity range given here
fadingTrailsSteps = 8 # Number of buckets to fade opacity through >= 3 hours old
opacityStepMin = 10
opacityStepMax = 60

replayMode = False
replayIncrement = 60 # seconds
replayMinTimestamp = 544853504 # Default to 0. Use to limit the start time of replays until something interesting happens

showCurrentBikePositions = False
# CONFIG END


# sqlitePath = "./data/bikes.sqlite"
sqlitePath = "./data/bikes.sqlite"
mapfilePath = "./bikes.map"
mapfileTemplate = "./bikes-template.map"
conn = db.connect(sqlitePath, timeout=3)
cur = conn.cursor()
lastSnapshotTimestamp = None
halfAnHour = 60 * 30
churchFrameNum = 19
churchFramePosition = 0
hourIncrementStart = 0
replayMaxTimestamp = None

def getMinTimestampAllBikes():
    sql = "SELECT MIN(timestamp) FROM bikes"
    cur.execute(sql)
    return cur.fetchone()[0]

def getCurrentBikePositions():
    sql = "SELECT bikeid, ST_X(PointN(geom, 2)), ST_Y(PointN(geom, 2)) FROM bikes GROUP BY bikeid ORDER BY timestamp DESC"
    if replayMode:
        sql = "SELECT bikeid, ST_X(PointN(geom, 2)), ST_Y(PointN(geom, 2)) FROM bikes WHERE timestamp <= %f GROUP BY bikeid ORDER BY timestamp DESC" % (replayMaxTimestamp)
    cur.execute(sql)

    bikePositions = {}
    for row in cur.fetchall():
        # bikePositions[row[0]] = {"lon": row[1], "lat": row[2]}
        bikePositions[row[0]] = "%f %f" % (row[1], row[2])
    return bikePositions

# Get min and max timestamps per bike
def getBikeTimestamps():
    global hourIncrementStart
    
    timestampsPerBike = {}
    # timestampsPerBikeFoo = {}
    # sql = "SELECT bikeid, MIN(timestamp), MAX(timestamp) FROM bikes GROUP BY bikeid"
    # for row in cur.execute(sql):
    #     timestampsPerBikeFoo[row[0]] = {
    #         "min": row[1],
    #         "max": row[2],
    #         "minThreshold": row[2] - (latestTrailsThresholdHours * 60 * 60) - (60 * 60 * hourIncrementStart)
    #     }
    
    # for bikeid in timestampsPerBikeFoo:
    #     sql = "SELECT bikeid, MIN(timestamp), MAX(timestamp) FROM bikes WHERE bikeid = %s AND timestamp >= %s GROUP BY bikeid" % (bikeid, timestampsPerBikeFoo[bikeid]["minThreshold"])
    #     # sql = "SELECT bikeid, MIN(timestamp), MAX(timestamp) FROM bikes WHERE bikeid = %s GROUP BY bikeid" % (bikeid)

    #     cur.execute(sql)
    #     res = cur.fetchone()
    #     timestampsPerBike[bikeid] = {
    #         "min": res[1],
    #         "max": res[2],
    #     }
    
    timestampsPerBike = {}
    sql = "SELECT bikeid, MIN(timestamp), MAX(timestamp) FROM bikes GROUP BY bikeid"
    if replayMode:
        sql = "SELECT bikeid, MIN(timestamp), MAX(timestamp) FROM bikes WHERE timestamp <= %d GROUP BY bikeid" % (replayMaxTimestamp)
        
    for row in cur.execute(sql):
        timestampsPerBike[row[0]] = {
            "min": row[1],
            "max": row[2],
        }
    return timestampsPerBike

# Create a mapfile with the correct styling rules for the current point in time
def createMapfile():
    global mapfilePath, mapfileTemplate, fadingTrailsSteps, churchFramePosition

    def getTemplateMapfile():
        with open(mapfileTemplate, "r") as f:
            template = f.read()
        return template
    
    # RGB
    bikeStyles = {
        1: {
            "colour": "251 176 59"
        },
        2: {
            "colour": "34 59 83"
        },
        3: {
            "colour": "229 94 94"
        },
        4: {
            "colour": "59 178 208"
        },
        5: {
            "colour": "204 204 204"
        },

        # Pastel Colours
        # 1: {
        #     # Yellow
        #     "colour": "255 210 77"
        # },
        # 2: {
        #     # Red
        #     "colour": "147 56 74"
        # },
        # 3: {
        #     # Dusky Blue
        #     "colour": "45 98 108"
        # },
        # 4: {
        #     # Purple
        #     "colour": "74 47 72"
        # },
        # 5: {
        #     # Pink
        #     "colour": "227 172 208"
        # },
    }

    bikeTrailsClassTemplateLatestNoTimestamp = """
        CLASS
            NAME "Bike {BIKEID}"
            EXPRESSION ([bikeid] eq {BIKEID})
            STYLE
                WIDTH 1
                COLOR {COLOUR_RGB}
                OPACITY {OPACITY}
            END
        END
    """

    bikeTrailsClassTemplateLatest = """
        CLASS
            NAME "Bike {BIKEID}"
            EXPRESSION ([bikeid] eq {BIKEID} AND [timestamp] >= {MINTIMESTAMP})
            STYLE
                WIDTH 1
                COLOR {COLOUR_RGB}
                OPACITY {OPACITY}
            END
        END
    """

    bikeTrailsClassTemplate = """
        CLASS
            NAME "Bike {BIKEID} ({HOURS})"
            EXPRESSION ([bikeid] eq {BIKEID} AND [timestamp] >= {MINTIMESTAMP} AND [timestamp] < {MAXTIMESTAMP})
            STYLE
                WIDTH 1
                COLOR {COLOUR_RGB}
                OPACITY {OPACITY}
            END
        END
    """

    bikeTrailsClassTemplateCurrentPosition = """
        LAYER
            NAME bike{BIKEID}currentposition
            TYPE POINT
            STATUS DEFAULT
            FEATURE
                POINTS
                    {BIKE_CURRENT_COORDS}
                END # End Points
            END # End Feature
            CLASS
                NAME "Bike {BIKEID} Current Position"
                STYLE
                    SYMBOL "circle"
                    SIZE 5
                    COLOR {COLOUR_RGB}
                    OPACITY {OPACITY}
                END
            END
        END
    """

    bikeClasses = []

    timestampsPerBike = getBikeTimestamps()
    print timestampsPerBike

    for bikeid in timestampsPerBike:
        print
        print "## Bikeid %s" % (bikeid)

        if noSteps:
            latestTrailsClass = bikeTrailsClassTemplateLatestNoTimestamp
            latestTrailsClass = latestTrailsClass.replace("{BIKEID}", str(bikeid))
            latestTrailsClass = latestTrailsClass.replace("{OPACITY}", "70")
            latestTrailsClass = latestTrailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
            bikeClasses.append(latestTrailsClass)

        else:
            # Latest = 100% opacity and trails from the last n hours
            latestMinTimestamp = timestampsPerBike[bikeid]["max"] - (latestTrailsThresholdHours * 60 * 60) + 1

            # latestTrailsClass = bikeTrailsClassTemplateLatest
            # latestTrailsClass = latestTrailsClass.replace("{BIKEID}", str(bikeid))
            # latestTrailsClass = latestTrailsClass.replace("{MINTIMESTAMP}", str(latestMinTimestamp))
            # latestTrailsClass = latestTrailsClass.replace("{OPACITY}", "70")
            # latestTrailsClass = latestTrailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
            # bikeClasses.append(latestTrailsClass)

            if onlyTwoSteps:
                # This works because MapServer matches the first class that it finds - so this catches everything older than latestTrailsClass
                latestTrailsClass = bikeTrailsClassTemplateLatestNoTimestamp
                latestTrailsClass = latestTrailsClass.replace("{BIKEID}", str(bikeid))
                latestTrailsClass = latestTrailsClass.replace("{OPACITY}", "50")
                latestTrailsClass = latestTrailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
                bikeClasses.append(latestTrailsClass)

            else:
                opacityStepMaxActual = opacityStepMax
                latestMinTimestamp = timestampsPerBike[bikeid]["max"]
                timestampDiff = latestMinTimestamp - timestampsPerBike[bikeid]["min"]
                timestampIncrementSeconds = int(round(timestampDiff / fadingTrailsSteps))

                # Opacity step size
                opacityIncrement = (opacityStepMaxActual - opacityStepMin) / fadingTrailsSteps

                stepsInHours = []
                timestampDiffRemaining = timestampDiff
                timestampDiffRemaining = float(timestampsPerBike[bikeid]["max"] - timestampsPerBike[bikeid]["min"])
                print "timestampDiffRemaining %s (%s)" % (timestampDiffRemaining, timestampDiffRemaining / (60 * 60))
                for step in reversed(range(1, fadingTrailsSteps + 1)):
                    haltStepping = False
                    # print "Step %s" % (step)

                    stepSize = timestampDiffRemaining / 2
                    timestampDiffRemaining -= stepSize

                    print "stepSize %s (%s)" % (stepSize, stepSize / (60 * 60))
                    if stepSize < (60 * 60 * 3):
                        haltStepping = True
                        # stepSize = (60 * 60 * 3)
                        stepSize = timestampDiffRemaining
                        print "Halt stepSize %s (%s)" % (stepSize, stepSize / (60 * 60))
                        
                    stepsInHours.append(stepSize / (60 * 60))

                    if haltStepping:
                        # print "Halt %s (%s)" % (timestampDiffRemaining, float(timestampDiffRemaining) / (60 * 60))
                        stepsInHours.append(float(timestampDiffRemaining) / (60 * 60))
                        break
                stepsInHours = list(reversed(stepsInHours))
                print stepsInHours

                stepStartMaxTimestamp = timestampsPerBike[bikeid]["max"]
                stepStartOpacity = opacityStepMaxActual
                timestampDiffRemaining = timestampDiff
                timestampDiffRemaining = timestampsPerBike[bikeid]["max"]
                for i, stepHours in enumerate(stepsInHours):
                    # print "Step %s (%shrs)" % (i, stepHours)

                    stepMinTimestamp = stepStartMaxTimestamp - (stepHours * (60 * 60))
                    if stepMinTimestamp < timestampsPerBike[bikeid]["min"]:
                        stepMinTimestamp = timestampsPerBike[bikeid]["min"]

                    stepOpacity = stepStartOpacity - opacityIncrement

                    trailsClass = bikeTrailsClassTemplate
                    trailsClass = trailsClass.replace("{BIKEID}", str(bikeid))
                    trailsClass = trailsClass.replace("{HOURS}", str(stepHours))
                    trailsClass = trailsClass.replace("{MINTIMESTAMP}", str(int(stepMinTimestamp)))
                    trailsClass = trailsClass.replace("{MAXTIMESTAMP}", str(int(stepStartMaxTimestamp)))
                    trailsClass = trailsClass.replace("{OPACITY}", str(stepOpacity))
                    trailsClass = trailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
                    bikeClasses.append(trailsClass)

                    stepStartMaxTimestamp = stepMinTimestamp
                    stepStartOpacity = stepOpacity

    template = getTemplateMapfile()

    with open(mapfilePath, "w") as f:
        content = template
        
        # Only the default bikes template with opacity fading needs {BIKE_CLASSES}
        if mapfileTemplate == "./bikes-template.map":
            content = content.replace("{BIKE_CLASSES}", "".join(bikeClasses))

        dataQuery = "bikes"
        if replayMode:
            dataQuery = "SELECT * FROM bikes WHERE timestamp <= %d" % (replayMaxTimestamp)
        content = content.replace("{DATA_QUERY}", dataQuery)

        if showCurrentBikePositions:
            bikePositions = getCurrentBikePositions()
            bikeCurrentClasses = []
            for bikeid in bikePositions:
                latestTrailsClassCurPos = bikeTrailsClassTemplateCurrentPosition
                latestTrailsClassCurPos = latestTrailsClassCurPos.replace("{BIKE_CURRENT_COORDS}", bikePositions[bikeid])
                latestTrailsClassCurPos = latestTrailsClassCurPos.replace("{BIKEID}", str(bikeid))
                latestTrailsClassCurPos = latestTrailsClassCurPos.replace("{OPACITY}", "70")
                latestTrailsClassCurPos = latestTrailsClassCurPos.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
                bikeCurrentClasses.append(latestTrailsClassCurPos)

            content = content.replace("{CURRENT_BIKE_LOCATIONS}", "".join(bikeCurrentClasses))
        else:
            content = content.replace("{CURRENT_BIKE_LOCATIONS}", "")

        content = content.replace("{CHURCH_FRAME_NUM}", str(churchFramePosition).zfill(5))

        churchFramePosition += 1
        if churchFramePosition > churchFrameNum:
            churchFramePosition = 0

        f.write(content)



if not os.path.isfile(sqlitePath):
    print "ERROR: Database %s doesn't exist." % (sqlitePath)

else:
    while True:
        mapserverOK = None
        hourIncrementStart += 1
        # print "Hour %s (Days %s)" % (hourIncrementStart, hourIncrementStart / 24)

        if replayMode:
            if replayMaxTimestamp == None:
                if replayMinTimestamp > 0:
                    replayMaxTimestamp = replayMinTimestamp + replayIncrement
                else:
                    replayMaxTimestamp = getMinTimestampAllBikes() + replayIncrement
            else:
                replayMaxTimestamp += replayIncrement
            # print "replayMaxTimestamp %d" % (replayMaxTimestamp)

        # Generate a new mapfile appropriate for the timestamps currently in the database
        # Used to fade features out over time
        createMapfile()

        if os.path.isfile("./bikes.tmp.png"):
            os.remove("./bikes.tmp.png")
        
        with open("./bikes.tmp.png", "w+") as f:
            ret = check_output(["mapserv", "-nh", "QUERY_STRING=map=" + mapfilePath + "&mode=map"])
            type = imghdr.what(None, h=ret)

            if type == "png":
                # All OK!
                mapserverOK = True
                f.write(ret)
            else:
                # Something wrong in MapServer-land!
                mapserverOK = False

                print "ERROR: MapServer returned a file of type '%s'! Using ./snapshots/map-latest.png instead." % (type)
                print ret
                print

                with open("./snapshots/map-latest.png", "r") as fl:
                    f.write(fl.read())

        # http://stackoverflow.com/questions/2333872/atomic-writing-to-file-with-python
        # tl;dr This doens't work on Windows or across different file systems.
        # If running on Windows we can't guarnatee atomic renaming, so comment this line (which throws an error) 
        # and uncomment the lines directly below.
        os.rename("./bikes.tmp.png", "./bikes.png")

        # For Windows ONLY
        # if os.path.isfile("./bikes.png"):
        #     os.remove("./bikes.png")
        # os.rename("./bikes.tmp.png", "./bikes.png")

        # Only snapshot if everything is OK in MapServer-land
        if mapserverOK == True:
            # Always take a snapshot the first time
            if lastSnapshotTimestamp == None or (datetime.utcnow() - lastSnapshotTimestamp) >  timedelta(minutes=snapshotInterval):
                print "Snapshot taken!"
                lastSnapshotTimestamp = datetime.utcnow()

                copyfile("./bikes.png", "./snapshots/map-%s.png" % (time.strftime("%Y-%m-%d-%H-%M-%S")))

                if os.path.isfile("./snapshots/map-latest.png"):
                    os.remove("./snapshots/map-latest.png")
                copyfile("./bikes.png", "./snapshots/map-latest.png")

            print "Map generated OK %s" % (time.strftime("%Y-%m-%d-%H-%M-%S"))
        
        sys.stdout.flush()
        time.sleep(sleepTime)

        exit()
    
    conn.close()