http://mapserver.org/cgi/mapserv.html

mapserv -nh "QUERY_STRING=map=./test.map&mode=map" > test.png
mapserv -nh "QUERY_STRING=map=./lines.map&mode=map" > test.png

mapserv -nh "QUERY_STRING=map=./bikes.map&mode=map" > test.png

CREATE VIEW "50_points_ts" AS
SELECT \* FROM "50_points" ORDER BY "timestamp" ASC

INSERT INTO geometry_columns ("f_table_name", "f_geometry_column", "geometry_type", "coord_dimension", "srid", "spatial_index_enabled") VALUES ("50_points_ts", "geometry", 1, 2, 0, 1)

ogr2ogr -f "SQLite" -sql "SELECT \* FROM 50-points.geojson.json" "50-points-ogr2ogr.sqlite" "50-points.geojson.json"

ogr2ogr -f "SQLite" -sql "SELECT \* FROM 50-points" "50-points-ogr2ogr.sqlite" "50-points.geojson.json"

ogr2ogr -f "SQLite" -sql "SELECT \* FROM '50_points' ORDER BY timestamp ASC" "50-points-ordered.sqlite" "50-points.sqlite"

ogr2ogr -f "SQLite" "29000-lines-ogr2ogr.sqlite" "29000-lines.json"

ogr2ogr -f "SQLite" -sql "SELECT \* FROM 'ogrgeojson' ORDER BY timestamp ASC" "29000-points-ordered.sqlite" "29000-lines-ogr2ogr.sqlite"
