<?php
// UPDATE topbikes SET lat = lat + RANDOM() / (18446744073709551616 * 16) + 0.03125, lon = lon + RANDOM() / (18446744073709551616 * 16) + 0.03125

$db = new SQLite3('bikes-all-years.db');

if(is_numeric($_GET['timestamp'])) {
    $stmt = $db->prepare('SELECT * FROM topbikes WHERE timestamp>=:timestamp');
    $stmt->bindValue(':timestamp', $_GET['timestamp'], SQLITE3_INTEGER);
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
   'type' => 'FeatureCollection',
   'crs' => $crs,
   'features' => array()
);

$rows = [];
while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
    $feature = array(
        'id' => $row['bikeid'] . $row['timestamp'],
        'type' => 'Feature', 
        'geometry' => array(
            'type' => 'Point',
            # Pass Longitude and Latitude Columns here
            'coordinates' => array($row['lon'] + mt_rand() / mt_getrandmax() / 50, $row['lat'] + mt_rand() / mt_getrandmax() / 50)
        ),
        # Pass other attribute columns here
        'properties' => array(
            'bikeid' => $row['bikeid'],
            'timestamp' => $row['timestamp'],
            // 'voltage' => $row['voltage'],
            )
        );

    # Add feature arrays to feature collection array
    array_push($geojson['features'], $feature);
}

// shuffle($geojson['features']);

// echo json_encode($rows);
echo json_encode($geojson, JSON_NUMERIC_CHECK);
?>