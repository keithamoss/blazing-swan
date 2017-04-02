<?php
$db = new SQLite3('bikes-all-years.db');

if(is_numeric($_GET['bikeid'])) {
    $stmt = $db->prepare("SELECT bikeid, MAX(timestamp) AS timestamp, group_concat(lon || \",\" || lat,  \";\") AS coordinates FROM topbikes WHERE bikeid=:bikeid ORDER BY timestamp ASC");
    $stmt->bindValue(':bikeid', $_GET['bikeid'], SQLITE3_INTEGER);
    $results = $stmt->execute();
} else {
    $results = $db->query("SELECT * FROM topbikes ORDER BY timestamp ASC");
}

header("Content-type: application/json");
ob_start('ob_gzhandler');

# Build GeoJSON feature collection array
$crs = new stdClass();
$crs->type = 'name';
$crs->properties = new stdClass();
$crs->properties->name = 'EPSG:4326';

$geojson = array(
   'type'      => 'FeatureCollection',
   'crs' => $crs,
   'features'  => array()
);

// $bikeIdsToColours = [
//     14946 => "#fbb03b",
//     17279 => "#223b53",
//     19054 => "#e55e5e",
//     20166 => "#3bb2d0",
//     20625 => "#ccc",
// ];

$bikeIdsToColours = [
    15731 => "#fbb03b",
    16941 => "#223b53",
    17526 => "#e55e5e",
    17747 => "#3bb2d0",
    20233 => "#ccc",
];

$points = [];
while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
    $points[] = $row;
}

$numPoints = count($points) - 1; // Skip the last point (the second last points draws to this one)
for($i = 0; $i < $numPoints; $i++) {
    $point = $points[$i];
    $nextPoint = $points[$i + 1];

    $coordinates = [];
    $coordinates[] = [$point['lon'], $point['lat']];
    $coordinates[] = [$nextPoint['lon'], $nextPoint['lat']];

    $feature = array(
        // 'id' => $point['bikeid'] . $point['timestamp'],
        'id' => $point['bikeid'],
        'type' => 'Feature', 
        'geometry' => array(
            'type' => 'LineString',
            # Pass Longitude and Latitude Columns here
            'coordinates' => $coordinates
        ),
        # Pass other attribute columns here
        'properties' => array(
            'bikeid' => $point['bikeid'],
            'timestamp' => $point['timestamp'],
            'colour' => $bikeIdsToColours[$point['bikeid']],
        )
    );
    # Add feature arrays to feature collection array
    array_push($geojson['features'], $feature);
}

echo json_encode($geojson, JSON_NUMERIC_CHECK);
?>