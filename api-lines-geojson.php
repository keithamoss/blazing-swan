<?php
$db = new SQLite3('bikes-all-years.db');

if(is_numeric($_GET['bikeid'])) {
    $stmt = $db->prepare("SELECT bikeid, MAX(timestamp) AS timestamp, group_concat(lon || \",\" || lat,  \";\") AS coordinates FROM topbikes WHERE bikeid=:bikeid ORDER BY timestamp ASC");
    $stmt->bindValue(':bikeid', $_GET['bikeid'], SQLITE3_INTEGER);
    $results = $stmt->execute();
} else {
    $results = $db->query("SELECT bikeid, MAX(timestamp) AS timestamp, group_concat(lon || \",\" || lat,  \";\") AS coordinates FROM topbikes GROUP BY bikeid ORDER BY timestamp ASC");
}

header("Content-type: application/json");
ob_start('ob_gzhandler');

# Build GeoJSON feature collection array
$geojson = array(
   'type'      => 'FeatureCollection',
   'features'  => array()
);

$bikeIdsToColours = [
    15731 => "#fbb03b",
    16941 => "#223b53",
    17526 => "#e55e5e",
    17747 => "#3bb2d0",
    20233 => "#ccc",
];

$rows = [];
while ($row = $results->fetchArray(SQLITE3_ASSOC)) {
    $coordinates = [];
    $coordinatePairs = explode(";", $row['coordinates']);
    foreach($coordinatePairs as $pair) {
        $boom = explode(",", $pair);
        $coordinates[] = [$boom[0] + mt_rand() / mt_getrandmax() / 50, $boom[1] + mt_rand() / mt_getrandmax() / 50];
    }

    $feature = array(
        'id' => $row['bikeid'],
        'type' => 'Feature', 
        'geometry' => array(
            'type' => 'LineString',
            # Pass Longitude and Latitude Columns here
            'coordinates' => $coordinates
        ),
        # Pass other attribute columns here
        'properties' => array(
            'bikeid' => $row['bikeid'],
            'timestamp' => $row['timestamp'],
            'colour' => $bikeIdsToColours[$row['bikeid']],
        )
    );
    # Add feature arrays to feature collection array
    array_push($geojson['features'], $feature);
}

echo json_encode($geojson, JSON_NUMERIC_CHECK);
?>