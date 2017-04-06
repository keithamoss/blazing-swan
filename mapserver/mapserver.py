from pyspatialite import dbapi2 as db
from subprocess import check_output
from shutil import copyfile
import os
import random
import time
import imghdr

# CONFIG START
sleepTime = 1 # seconds - time to sleep after generating a map image
snapshotInterval = 10 # minutes - how often snapshots are saved to ./snapshots

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
# CONFIG END

# sqlitePath = "./data/bikes.sqlite"
sqlitePath = "./data/bikes.sqlite"
mapfilePath = "./bikes.map"
mapfileTemplate = "./bikes-template.map"
conn = db.connect(sqlitePath, timeout=3)
cur = conn.cursor()
snapshotCounter = None
halfAnHour = 60 * 30
churchFrameNum = 19
churchFramePosition = 0

# Get min and max timestamps per bike
def getBikeTimestamps():
    timestampsPerBike = {}
    sql = "SELECT bikeid, MIN(timestamp), MAX(timestamp) FROM bikes GROUP BY bikeid"
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

        # 20233: {
        #     "colour": "251 176 59"
        # },
        # 17747: {
        #     "colour": "34 59 83"
        # },
        # 15731: {
        #     "colour": "229 94 94"
        # },
        # 16941: {
        #     "colour": "59 178 208"
        # },
        # 17526: {
        #     "colour": "204 204 204"
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
            NAME "Bike {BIKEID}"
            EXPRESSION ([bikeid] eq {BIKEID} AND [timestamp] >= {MINTIMESTAMP} AND [timestamp] < {MAXTIMESTAMP})
            STYLE
                WIDTH 1
                COLOR {COLOUR_RGB}
                OPACITY {OPACITY}
            END
        END
    """

    bikeClasses = []

    timestampsPerBike = getBikeTimestamps()
    # print timestampsPerBike

    for bikeid in timestampsPerBike:
        # print bikeid

        if noSteps:
            latestTrailsClass = bikeTrailsClassTemplateLatestNoTimestamp
            latestTrailsClass = latestTrailsClass.replace("{BIKEID}", str(bikeid))
            latestTrailsClass = latestTrailsClass.replace("{OPACITY}", "70")
            latestTrailsClass = latestTrailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
            # print latestTrailsClass
            bikeClasses.append(latestTrailsClass)

        else:
            # Latest = 100% opacity and trails from the last n hours
            latestMinTimestamp = timestampsPerBike[bikeid]["max"] - (latestTrailsThresholdHours * 60 * 60) + 1

            latestTrailsClass = bikeTrailsClassTemplateLatest
            latestTrailsClass = latestTrailsClass.replace("{BIKEID}", str(bikeid))
            latestTrailsClass = latestTrailsClass.replace("{MINTIMESTAMP}", str(latestMinTimestamp))
            latestTrailsClass = latestTrailsClass.replace("{OPACITY}", "70")
            latestTrailsClass = latestTrailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
            # print latestTrailsClass
            bikeClasses.append(latestTrailsClass)

            if onlyTwoSteps:
                # This works because MapServer matches the first class that it finds - so this catches everything older than latestTrailsClass
                latestTrailsClass = bikeTrailsClassTemplateLatestNoTimestamp
                latestTrailsClass = latestTrailsClass.replace("{BIKEID}", str(bikeid))
                latestTrailsClass = latestTrailsClass.replace("{OPACITY}", "50")
                latestTrailsClass = latestTrailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
                # print latestTrailsClass
                bikeClasses.append(latestTrailsClass)

            else:
                # timestampsPerBike[bikeid]["min"] = latestMinTimestamp - (60 * 30)

                # Throw every after the last 3 hours into buckets
                # print "opacityStepMin %s" % (opacityStepMin)
                opacityStepMinActual = opacityStepMin
                # print "opacityStepMinActual %s" % (opacityStepMinActual)
                timestampDiff = latestMinTimestamp - timestampsPerBike[bikeid]["min"]
                # print "timestampDiff = %s" % (timestampDiff)
                timestampIncrementSeconds = int(round(timestampDiff / fadingTrailsSteps))
                # timestampIncrementSeconds = max(timestampIncrementSeconds, 60 * 60) # Each increment must be at least one hour
                # print "timestampIncrementSeconds = %s" % (timestampIncrementSeconds)

                # Opacity step size
                opacityIncrement = (opacityStepMax - opacityStepMinActual) / fadingTrailsSteps

                # Minimum step size of 1 hour
                # if timestampIncrementSeconds < (60 * 60):
                #     fadingTrailsSteps = 1
                    
                stepStartMinTimestamp = timestampsPerBike[bikeid]["min"]
                stepTimestampCounter = latestMinTimestamp
                stepStartOpacity = opacityStepMinActual
                for step in range (1, fadingTrailsSteps + 1):
                    # print "Step %s" % (step)
                    # latestMinTimestamp -= timestampDiff

                    # stepMinTimestamp = timestampsPerBike[bikeid]["min"]
                    stepMaxTimestamp = stepStartMinTimestamp + timestampIncrementSeconds

                    stepOpacity = stepStartOpacity + opacityIncrement
                    # print "stepOpacity %s" % (stepOpacity)
                    # stepOpacity = 10

                    trailsClass = bikeTrailsClassTemplate
                    trailsClass = trailsClass.replace("{BIKEID}", str(bikeid))
                    trailsClass = trailsClass.replace("{MINTIMESTAMP}", str(stepStartMinTimestamp))
                    trailsClass = trailsClass.replace("{MAXTIMESTAMP}", str(stepMaxTimestamp))
                    trailsClass = trailsClass.replace("{OPACITY}", str(stepOpacity))
                    trailsClass = trailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
                    # print trailsClass
                    bikeClasses.append(trailsClass)

                    # if (latestMinTimestamp - timestampDiff) < 0:
                    #     break

                    stepStartMinTimestamp = stepMaxTimestamp + 1
                    stepStartOpacity = stepOpacity
        
        # print

    template = getTemplateMapfile()
    # print template
    # print "\n\n".join(bikeClasses)

    with open(mapfilePath, "w") as f:
        content = template
        
        # Only generate a new mapfile if we're using bikes.map
        if mapfileTemplate == "./bikes-template.map":
            content = content.replace("{BIKE_CLASSES}", "".join(bikeClasses))

        content = content.replace("{CHURCH_FRAME_NUM}", str(churchFramePosition).zfill(5))
        churchFramePosition += 1
        if churchFramePosition > churchFrameNum:
            churchFramePosition = 0

        f.write(content)



if not os.path.isfile(sqlitePath):
    print "Error: Database %s doesn't exist." % (sqlitePath)

else:
    while True:
        mapserverOK = None

        # Always take a snapshot the first time we run
        if snapshotCounter == None:
            snapshotCounter = snapshotInterval * 60
        else:
            snapshotCounter += 1

        # Generate a new mapfile appropriate for the timestamps currently in the database
        # Used to fade features out over time
        createMapfile()

        if os.path.isfile("./bikes.tmp.png"):
            os.remove("./bikes.tmp.png")
        
        with open("./bikes.tmp.png", "w+") as f:
            ret = check_output(["mapserv", "-nh", "QUERY_STRING=map=" + mapfilePath + "&mode=map"])
            # print ret
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
            if (snapshotCounter * sleepTime) >= (snapshotInterval * 60):
                print "Snapshot taken!"
                snapshotCounter = 0

                copyfile("./bikes.png", "./snapshots/map-%s.png" % (time.strftime("%Y-%m-%d-%H-%M-%S")))

                if os.path.isfile("./snapshots/map-latest.png"):
                    os.remove("./snapshots/map-latest.png")
                copyfile("./bikes.png", "./snapshots/map-latest.png")
            # else:
            #     print "Snapshot pending! (%s vs %s)" % ((snapshotCounter * sleepTime), (snapshotInterval * 60))

            print "Map generated OK."
        time.sleep(sleepTime)

        # exit()
    
    # conn.close()