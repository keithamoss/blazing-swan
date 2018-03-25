# Changelog

## 2017

Hacked together with gaffer tape and prayer in a few days. Surprised it actually held up and worked.

## 2018

The 2018 version of CycleSchema cleans up a bit of 2017's hacky mess and adds a new feature - animated theme camps with a geofence that causes them to power up/on/off in response to the position of the bikes.

At the time of writing we don't yet have the final animations for the theme camps, so `mapsever/config.py` only contains an example of a theme camp.

To change the position of a theme camp simply edit the `lon` and `lat` variables for the given camp in `maperver/config.py`, then stop and start the python MapServer process.

The theme camps feature is only active if Mode 2 or 3 discussed below are activated.

# Configuration

## Available Modes

There are three modes available for CycleSchema that primarily differ in how and where we control animating the theme camps.

### Mode 1: Do it all on the backend (aka CycleSchema 2017 Mode)

In this mode all processing is done on the backend (in MapServer controlled via Python) and the frontend `index-mapserver.html` is merely a simple webpage that refreshes the background image every so often. Very simple technically, but it does mean that animations (e.g. Church of Belligerence) end up appearing quite jerky because we aren't able to regenerate and refresh the image from MapServer often enough to make them appear smooth enough for the human eye.

Set the following values in `mapserver/config.py` -

```python
sleepTime = 0.5
snapshotInterval = 10
showCurrentBikePositions = False
showAnimatedCamps = False
showAnimatedChurchOfBelligerence = True
```

With this setup run CycleSchema and open http://localhost:8000/index-mapserver.html.

### Mode 2: Do it all on the backend and show animated theme camps

Mode 2 is really Mode 1, but with animated theme camps that will power up and down in response to bikes being nearby.

To setup this mode set all variables as per Mode 1 above, but with the following values set in `mapserver/config.py` -

```python
sleepTime = 0.25
geofenceRadiusInMetres = 50
showAnimatedCamps = True
showAnimatedChurchOfBelligerence = False
```

**NB:** This may be a little confusing - `showAnimatedCamps = True` also takes care of animating the Church of Belligerence. `showAnimatedChurchOfBelligerence` is kept around for legacy reasons, and can safely be turned off if we're using the new `showAnimatedCamps` capability.

With this setup run CycleSchema and open http://localhost:8000/index-mapserver.html.

### Mode 3: Handle animations on the frontend (Default mode)

This is a new mode for 2018 that works more like a traditional web map and lets us more smoothly animate the theme camps and the Church of Belligerence. As with Mode 2, the camps will show different animations for powering up/on/down in response to bikes being nearby. In this mode we only rely on the MapServer backend to show the positions and trails of the bikes moving about.

Set the following values in `mapserver/config.py` -

```python
sleepTime = 0.5
snapshotInterval = 10
showCurrentBikePositions = False
geofenceRadiusInMetres = 50
showAnimatedCamps = False
showAnimatedChurchOfBelligerence = False
```

With this setup run CycleSchema and open http://localhost:8000/index-leaflet.html.

There are config options available in `cycleschema-leaflet.js` that you may need or want to tweak. Refer to the documentation at the top of the file and edit the `config` variable.

## Running CycleSchema

For the MapServer backend open a terminal window and run this from the root directory -

```
. venv/bin/activate
cd mapserver
python mapserver.py
```

For the PHP backend open another terminal window and run this from the root directory -

`php -S localhost:8000`

# Development

## Extracting PNG frames from an animated GIF

`convert -coalesce pin-eye2.gif pin_eye_%05d.png`

Requires Imagemagick to be installed.

## Converting PNG frames into an animated GIF

`convert -delay 10 -loop 0 *.png animation.gif`

# Installation

1.  Install PHP

2.  Create a Python virtual environment and install from `requirements.txt`

3.  Download and unzip [this repo](https://github.com/keithamoss/blazing-swan/archive/master.zip)

4.  Choose a mode and follow instructions from "Running CycleSchema" above.

## Spatialite

Trouble installing Pyspatialite? You probably need to instal `proj` and `geos` and set your `CFLAGS` environment variable correctly before installing it.

1.  `brew install proj geos` (macOS only)

2.  `CFLAGS="-I/usr/local/Cellar/proj/4.9.3/include -I/usr/local/Cellar/geos/3.6.2/include" pip install --pre pyspatialite` (You may need to adjust the version numbers to match the current versions of Proj and Geos)

### Research

https://github.com/lokkju/pyspatialite/issues/18

Pyspatialite 2.6.2-spatialite.2.4.0-4 and 2.6.2-spatialite.2.3.1 both have bugs.

If we do a 2019 version lets replace Pyspatialite with something more modern!

# Initial Project Research

https://www.mapbox.com/mapbox-gl-js/example/data-driven-lines/
https://www.mapbox.com/mapbox-gl-js/style-spec/#layer-paint
https://www.mapbox.com/help/gl-dds-ref/

https://github.com/mapbox/mapbox-gl-js/issues/1764
https://github.com/mapbox/mapbox-gl-js/pull/380
https://github.com/mapbox/mapbox-gl-js/issues/61

http://openlayers.org/en/latest/examples/symbol-atlas-webgl.html
