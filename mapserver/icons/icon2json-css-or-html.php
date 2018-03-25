<?php
$camps = json_decode(file_get_contents("../camps.json"));

$json = [];

foreach($camps as $icon) {
  $json[$icon->name] = [
    "name" => $icon->name,
    "states" => $icon->states,
    "frames" => new stdClass(),
  ];

  // Camp is affected by bikes - apply animation logic for powering up/on/down/off
  if($icon->triggered_by_bikes === true) {
    for($frame = $icon->states->powered_off->frame_start; $frame <= $icon->states->powering_down->frame_end; $frame++) {
      $frame_number = str_pad($frame, 5, "0", STR_PAD_LEFT);
      $frame_url = $icon->base_url . "_" . $frame_number . ".png";
    
      $json[$icon->name]["frames"]->$frame = "data:image/png;base64," . base64_encode(file_get_contents($frame_url));
    }

  } else {
  // Camp is not affected by bikes - just loop its powered on animation
    for($frame = $icon->states->powered_on->frame_start; $frame <= $icon->states->powered_on->frame_end; $frame++) {
      $frame_number = str_pad($frame, 5, "0", STR_PAD_LEFT);
      $frame_url = $icon->base_url . "_" . $frame_number . ".png";
    
      $json[$icon->name]["frames"]->$frame = "data:image/png;base64," . base64_encode(file_get_contents($frame_url));
    }
  }
}

if(isset($_GET["html"])) {
  foreach($json as $icon) {
    foreach($icon["frames"] as $frame_num => $datauri) {
      echo '<img src="' . $datauri . '" class="' . $icon->name . '_' . $frame_num . '" width="66" height="50" />';
      echo "\n";
    }
  }

} elseif(isset($_GET["css"])) {
  header("Content-type: text/css");
  echo <<<EOT
      .leaflet-marker-pane img {
        cursor: default;
      }

EOT;

  foreach($json as $icon) {
//     echo <<<EOT
//         .{$icon["name"]} {
//           display: none;
//         }

// EOT;

    foreach($icon["frames"] as $frame_num => $datauri) {
      echo <<<EOT
        .{$icon["name"]}_{$frame_num} {
          content: url($datauri);
        }

EOT;
    }
  }

} else {
  header("Content-type: application/json");
  echo json_encode($json);
  // echo "var camps = " . json_encode($json) . ";";
}
?>