## Master Control
sleepTime = 0.1 # seconds - time to sleep after generating a map image
snapshotInterval = 10 # minutes - how often snapshots are saved to ./snapshots

## Config for styling the bikes
showCurrentBikePositions = True

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


## Config for camp animation
showAnimatedCamps = False
geofenceRadiusInMetres = 50


## Config for replay mode
replayMode = True
replayIncrement = 60 # seconds
replayMinTimestamp = 545305309 # Default to 0. Use to limit the start time of replays until something interesting happens


## Config For Testing Only
# Test Case 1: Pop-up and then Pop-away after 4 frames
# Bike 4 with Camp 1 at 118.329704 -32.660247
# replayIncrement = 20
# replayMinTimestamp = 545307309

# Test Case 2: Power up, be powered on, then power off
# Bike 1 with Camp 1 at 118.332082 -32.657582
replayIncrement = 5
replayMinTimestamp = 545307309

# Test Case 3: Go through two attempts at powering up before being powered down
# Bike 5 with Camp 1 at 118.330937 -32.657042
# replayIncrement = 5
# replayMinTimestamp = 545353900


## Camps
camps = [
    {
        "name": "camp1",
        "base_url": "camp1/campfire_",
        "icon_width": 64,
        "icon_height": 64,
        # Test Case 1
        # "lon": 118.329704,
        # "lat": -32.660247,
        # Test Case 2
        "lon": 118.332082,
        "lat": -32.657582,
        # Test Case 3
        # "lon": 118.330937,
        # "lat": -32.657042,
        "current_frame": 0,
        "current_state": "POWERED_DOWN",
        "states": {
            "powered_off": {
                "frame_start": 0,
            },
            "powering_up": {
                "frame_start": 1,
                "frame_end": 60,
            },
            "powered_on": {
                "frame_start": 61,
                "frame_end": 104,
            },
            "powering_down": {
                "frame_start": 105,
                "frame_end": 149,
            }
        },
    }
]