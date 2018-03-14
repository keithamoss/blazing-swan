from pyspatialite import dbapi2 as db
from subprocess import check_output
from shutil import copyfile
import os
import random
import time
from datetime import datetime, timedelta
import imghdr
import sys

import config

# sqlitePath = "./data/bikes.sqlite"
sqlitePath = "./data/2017_actual/bikes.sqlite"
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

def initCamps():
    global config
    return config.camps

def getCountOfBikesNearCamps(timestampsPerBike):
    state = {}

    for camp in camps:
        bikeSQL = []
        for bikeid in timestampsPerBike:
            data = timestampsPerBike[bikeid]

            sql = "(bikeid = %d AND timestamp >= %d AND PtDistWithin(SetSRID(PointFromText('%s'), 4326), SetSRID(PointFromText('POINT(%f %f)'), 4326), %d, 1))" % (bikeid, data["max"], data["point"], camp["lon"], camp["lat"], config.geofenceRadiusInMetres)
            if config.replayMode:
                sql = "(bikeid = %d AND timestamp >= %d AND timestamp <= %d AND PtDistWithin(SetSRID(PointFromText('%s'), 4326), SetSRID(PointFromText('POINT(%f %f)'), 4326), %d, 1))" % (bikeid, data["max"], replayMaxTimestamp, data["point"], camp["lon"], camp["lat"], config.geofenceRadiusInMetres)
            bikeSQL.append(sql)
            # print sql

        for row in cur.execute("SELECT COUNT(*) FROM bikes WHERE " + " OR ".join(bikeSQL)):
            state[camp["name"]] = row[0]

    return state

def animateCamps(camps, content, timestampsPerBike):
    def setPoweredOffFrame():
        camp["current_state"] = "POWERED_DOWN"
        camp["current_frame"] = camp["states"]["powered_off"]["frame_start"]

    def beginPowerUpAni():
        camp["current_state"] = "POWERING_UP"
        camp["current_frame"] = camp["states"]["powering_up"]["frame_start"]
    
    def tickPowerUpAni():
        camp["current_state"] = "POWERING_UP"
        camp["current_frame"] += 1

        if camp["current_frame"] > camp["states"]["powering_up"]["frame_end"]:
            camp["current_state"] = "POWERED_ON"
    
    def reversePowerUpAni():
        camp["current_state"] = "POWERING_UP"
        camp["current_frame"] -= 1

        if camp["current_frame"] <= camp["states"]["powering_up"]["frame_start"]:
            camp["current_state"] = "POWERED_DOWN"
    
    def loopPoweredOnAni():
        camp["current_state"] = "POWERED_ON"
        camp["current_frame"] += 1

        if camp["current_frame"] > camp["states"]["powered_on"]["frame_end"]:
            camp["current_frame"] = camp["states"]["powered_on"]["frame_start"]

    def beginPowerDownAni():
        camp["current_state"] = "POWERING_DOWN"
        camp["current_frame"] = camp["states"]["powering_down"]["frame_start"]
    
    def beginPowerDownAniASAP():
        halfwayPoint = camp["states"]["powered_on"]["frame_start"] + ((camp["states"]["powered_on"]["frame_end"] - camp["states"]["powered_on"]["frame_start"]) / 2)

        if camp["current_frame"] <= halfwayPoint:
            camp["current_frame"] -= 1

            if camp["current_frame"] < camp["states"]["powered_on"]["frame_start"]:
                beginPowerDownAni()

        else:
            camp["current_frame"] += 1

            if camp["current_frame"] > camp["states"]["powered_on"]["frame_end"]:
                beginPowerDownAni()
    
    # def beginPowerDownAniWhenNextLoopFinishes():
    #     camp["current_frame"] += 1
    
    #     if camp["current_frame"] > camp["states"]["powered_on"]["frame_end"]:
    #         beginPowerDownAni()
    
    def tickPowerDownAni():
        camp["current_state"] = "POWERING_DOWN"
        camp["current_frame"] += 1

        if camp["current_frame"] >= camp["states"]["powering_down"]["frame_end"]:
            camp["current_state"] = "POWERED_DOWN"
    
    def reversePowerDownAni():
        camp["current_state"] = "POWERING_DOWN"
        camp["current_frame"] -= 1

        if camp["current_frame"] <= camp["states"]["powering_down"]["frame_start"]:
            camp["current_state"] = "POWERED_ON"
            camp["current_frame"] = camp["states"]["powered_on"]["frame_start"]


    bikeCount = getCountOfBikesNearCamps(timestampsPerBike)
    # print bikeCount

    for camp in camps:
        # Set the position of the camp (during dev only?)
        campLatPlaceholderString = "{%s_LAT}" % camp["name"].upper()
        campLonPlaceholderString = "{%s_LON}" % camp["name"].upper()
        content = content.replace(campLatPlaceholderString, str(camp["lat"]))
        content = content.replace(campLonPlaceholderString, str(camp["lon"]))

        if bikeCount[camp["name"]] > 0:
            if camp["current_state"] == "POWERED_DOWN":
                beginPowerUpAni()
            elif camp["current_state"] == "POWERING_UP":
                tickPowerUpAni()
            elif camp["current_state"] == "POWERED_ON":
                loopPoweredOnAni()
            elif camp["current_state"] == "POWERING_DOWN":
                # Keep the animations graceful by reversing the powering down ani
                # if bikes rejoin the camp while we're still powering down
                reversePowerDownAni()
        else:
            if camp["current_state"] == "POWERING_UP":
                # Keep the animations graceful by reversing the powering up ani
                # if bikes leave the camp while we're still powering up
                reversePowerUpAni()
            elif camp["current_state"] == "POWERED_ON":
                beginPowerDownAniASAP()
            elif camp["current_state"] == "POWERING_DOWN":
                tickPowerDownAni()
            elif camp["current_state"] == "POWERED_DOWN":
                setPoweredOffFrame()

        campFramePlaceholderString = "{%s_FRAME_NUM}" % camp["name"].upper()
        content = content.replace(campFramePlaceholderString, str(camp["current_frame"]).zfill(5))

        print "%s (Bikes = %s; Frame = %s; State = %s)" % (camp["name"], bikeCount[camp["name"]], camp["current_frame"], camp["current_state"])
    # exit()

    return content

def getMinTimestampAllBikes():
    sql = "SELECT MIN(timestamp) FROM bikes"
    cur.execute(sql)
    return cur.fetchone()[0]

def getMaxTimestampAllBikes():
    sql = "SELECT MAX(timestamp) FROM bikes"
    cur.execute(sql)
    return cur.fetchone()[0]

def getCurrentBikePositions():
    sql = "SELECT bikeid, ST_X(PointN(geom, 2)), ST_Y(PointN(geom, 2)) FROM bikes GROUP BY bikeid ORDER BY timestamp DESC"
    if config.replayMode:
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
    #         "minThreshold": row[2] - (config.latestTrailsThresholdHours * 60 * 60) - (60 * 60 * hourIncrementStart)
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
    sql = "SELECT bikeid, MIN(timestamp), MAX(timestamp), ST_AsText(EndPoint(geom)) FROM bikes GROUP BY bikeid"
    if config.replayMode:
        sql = "SELECT bikeid, MIN(timestamp), MAX(timestamp), ST_AsText(EndPoint(geom)) FROM bikes WHERE timestamp <= %d GROUP BY bikeid" % (replayMaxTimestamp)
        
    for row in cur.execute(sql):
        timestampsPerBike[row[0]] = {
            "min": row[1],
            "max": row[2],
            "point": row[3],
        }
    return timestampsPerBike

# Create a mapfile with the correct styling rules for the current point in time
def createMapfile():
    global mapfilePath, mapfileTemplate, config, churchFramePosition

    def getTemplateMapfile():
        with open(mapfileTemplate, "r") as f:
            template = f.read()
        return template
    
    # RGB
    bikeStyles = {
        1: {
            # Orange
            "colour": "251 176 59"
        },
        2: {
            # Dusky Blue
            "colour": "34 59 83"
        },
        3: {
            # Salmon Pink
            "colour": "229 94 94"
        },
        4: {
            # Light Blue
            "colour": "59 178 208"
        },
        5: {
            # Grey
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
            NAME "Bike {BIKEID} ({HOURS} hours)"
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
            NAME "Bike {BIKEID} ({HOURS} hours)"
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
    # print timestampsPerBike

    for bikeid in timestampsPerBike:
        # print
        # print "## Bikeid %s" % (bikeid)

        if config.noSteps:
            latestTrailsClass = bikeTrailsClassTemplateLatestNoTimestamp
            latestTrailsClass = latestTrailsClass.replace("{BIKEID}", str(bikeid))
            latestTrailsClass = latestTrailsClass.replace("{OPACITY}", "70")
            latestTrailsClass = latestTrailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
            bikeClasses.append(latestTrailsClass)

        else:
            # Latest = 100% opacity and trails from the last n hours
            latestMinTimestamp = timestampsPerBike[bikeid]["max"] - (config.latestTrailsThresholdHours * 60 * 60) + 1

            latestTrailsClass = bikeTrailsClassTemplateLatest
            latestTrailsClass = latestTrailsClass.replace("{BIKEID}", str(bikeid))
            latestTrailsClass = latestTrailsClass.replace("{HOURS}", str(config.latestTrailsThresholdHours))
            latestTrailsClass = latestTrailsClass.replace("{MINTIMESTAMP}", str(latestMinTimestamp))
            latestTrailsClass = latestTrailsClass.replace("{OPACITY}", "70")
            latestTrailsClass = latestTrailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
            bikeClasses.append(latestTrailsClass)

            if config.onlyTwoSteps:
                # This works because MapServer matches the first class that it finds - so this catches everything older than latestTrailsClass
                latestTrailsClass = bikeTrailsClassTemplateLatestNoTimestamp
                latestTrailsClass = latestTrailsClass.replace("{BIKEID}", str(bikeid))
                latestTrailsClass = latestTrailsClass.replace("{OPACITY}", "50")
                latestTrailsClass = latestTrailsClass.replace("{COLOUR_RGB}", bikeStyles[bikeid]["colour"])
                bikeClasses.append(latestTrailsClass)

            else:
                opacityStepMaxActual = config.opacityStepMax
                timestampDiff = latestMinTimestamp - timestampsPerBike[bikeid]["min"]
                timestampIncrementSeconds = int(round(timestampDiff / config.fadingTrailsSteps))

                # Opacity step size
                opacityIncrement = (opacityStepMaxActual - config.opacityStepMin) / config.fadingTrailsSteps

                stepsInHours = []
                timestampDiffRemaining = timestampDiff
                for step in reversed(range(1, config.fadingTrailsSteps + 1)):
                    haltStepping = False
                    # print "Step %s" % (step)

                    stepSize = timestampDiffRemaining / 2
                    timestampDiffRemaining -= stepSize

                    if stepSize < (60 * 60 * 3):
                        haltStepping = True
                        # stepSize = (60 * 60 * 3)
                        
                    stepsInHours.append(float(stepSize) / (60 * 60))

                    if haltStepping:
                        # print "Halting %s (%s)" % (timestampDiffRemaining, float(timestampDiffRemaining) / (60 * 60))
                        stepsInHours.append(float(timestampDiffRemaining) / (60 * 60))
                        break
                stepsInHours = list(reversed(stepsInHours))


                stepStartMaxTimestamp = latestMinTimestamp
                stepStartOpacity = opacityStepMaxActual
                timestampDiffRemaining = timestampDiff
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

        content = content.replace("{SQLITE_DB_PATH}", sqlitePath.replace("./data/", ""))
        
        # Only the default bikes template with opacity fading needs {BIKE_CLASSES}
        if mapfileTemplate == "./bikes-template.map":
            content = content.replace("{BIKE_CLASSES}", "".join(bikeClasses))

        dataQuery = "bikes"
        if config.replayMode:
            dataQuery = "SELECT * FROM bikes WHERE timestamp <= %d" % (replayMaxTimestamp)
        content = content.replace("{DATA_QUERY}", dataQuery)

        if config.showCurrentBikePositions:
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


        # Church of Belligerence
        content = content.replace("{CHURCH_FRAME_NUM}", str(churchFramePosition).zfill(5))
        churchFramePosition += 1
        if churchFramePosition > churchFrameNum:
            churchFramePosition = 0
        
        # Animate theme camps if bikes are close by
        content = animateCamps(camps, content, timestampsPerBike)

        f.write(content)



if not os.path.isfile(sqlitePath):
    print "ERROR: Database %s doesn't exist." % (sqlitePath)

else:
    maxTimestampAllBikes = getMaxTimestampAllBikes()

    # Some debug
    # for row in cur.execute("SELECT *, ST_AsText(geom) FROM bikes GROUP BY bikeid ORDER BY timestamp DESC"):
    #     print(row)
    # exit()
    
    camps = initCamps()
    
    while True:
        mapserverOK = None
        hourIncrementStart += 1
        # print "Hour %s (Days %s)" % (hourIncrementStart, hourIncrementStart / 24)

        if config.replayMode:
            if replayMaxTimestamp == None:
                if config.replayMinTimestamp > 0:
                    replayMaxTimestamp = config.replayMinTimestamp + config.replayIncrement
                else:
                    replayMaxTimestamp = getMinTimestampAllBikes() + config.replayIncrement
            else:
                replayMaxTimestamp += config.replayIncrement
            
            if replayMaxTimestamp > maxTimestampAllBikes:
                print "Fin"
                exit()
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
            if lastSnapshotTimestamp == None or (datetime.utcnow() - lastSnapshotTimestamp) >  timedelta(minutes=config.snapshotInterval):
                print "Snapshot taken!"
                lastSnapshotTimestamp = datetime.utcnow()

                copyfile("./bikes.png", "./snapshots/map-%s.png" % (time.strftime("%Y-%m-%d-%H-%M-%S")))

                if os.path.isfile("./snapshots/map-latest.png"):
                    os.remove("./snapshots/map-latest.png")
                copyfile("./bikes.png", "./snapshots/map-latest.png")

            # print "Map generated OK %s" % (time.strftime("%Y-%m-%d-%H-%M-%S"))
        
        sys.stdout.flush()
        time.sleep(config.sleepTime)

        # exit()
    
    conn.close()