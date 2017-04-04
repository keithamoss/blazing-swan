# Installation
1. Install PHP

2. Download and unzip [this repo](https://github.com/keithamoss/blazing-swan/archive/master.zip)

3. Navigate to the root of the repository and run `php -s localhost:8000`

4. Point your browser at one of the HTML pages e.g. [trails-points.html](http://localhost:8000/trails-points.html)


# Research
https://www.mapbox.com/mapbox-gl-js/example/data-driven-lines/
https://www.mapbox.com/mapbox-gl-js/style-spec/#layer-paint
https://www.mapbox.com/help/gl-dds-ref/

https://github.com/mapbox/mapbox-gl-js/issues/1764
https://github.com/mapbox/mapbox-gl-js/pull/380
https://github.com/mapbox/mapbox-gl-js/issues/61

http://openlayers.org/en/latest/examples/symbol-atlas-webgl.html

# Spatialite
https://github.com/lokkju/pyspatialite/issues/18

`brew install proj geos`

CFLAGS="-I/usr/local/Cellar/proj/4.9.2/include -I/usr/local/Cellar/geos/3.5.0/include" pip install --pre pyspatialite

pip install pyspatialite==2.6.2-spatialite.2.4.0-4
Fucked.

pip install pyspatialite==2.6.2-spatialite.2.3.1