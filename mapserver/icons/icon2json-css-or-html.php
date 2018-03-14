<?php
$icons = [[
  "icon_name" => "pin_eye",
  "base_url" => "pin_eye_png/pin_eye_",
  "frame_start" => 0,
  "frame_end" => 57,
  "boundaries" => [
    [
      "name" => "powering_up",
      "frame_start" => 0,
      "frame_end" => 15,
    ],
    [
      "name" => "powered_up",
      "frame_start" => 16,
      "frame_end" => 40,
    ],
    [
      "name" => "powering_down",
      "frame_start" => 41,
      "frame_end" => 57,
    ]
  ],
]];
$json = [];

foreach($icons as $icon) {
  $json[$icon["icon_name"]] = [
    "icon_name" => $icon["icon_name"],
    "boundaries" => $icon["boundaries"],
    "frames" => new stdClass(),
  ];

  for($frame = $icon["frame_start"]; $frame <= $icon["frame_end"]; $frame++) {
    $frame_number = str_pad($frame, 5, "0", STR_PAD_LEFT);
    $frame_url = $icon["base_url"] . $frame_number . ".png";
  
    $json[$icon["icon_name"]]["frames"]->$frame = "data:image/png;base64," . base64_encode(file_get_contents($frame_url));
  }
}

if(isset($_GET["html"])) {
  foreach($json as $icon) {
    foreach($icon["frames"] as $frame_num => $datauri) {
      echo '<img src="' . $datauri . '" class="' . $icon["icon_name"] . '_' . $frame_num . '" width="66" height="50" />';
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
    echo <<<EOT
        .{$icon["icon_name"]} {
          display: none;
        }

EOT;

    foreach($icon["frames"] as $frame_num => $datauri) {
      echo <<<EOT
        .{$icon["icon_name"]}_{$frame_num} {
          content: url($datauri);
        }

EOT;
    }
  }

} else {
  header("Content-type: application/json");
  echo json_encode($json);
  // echo "var icons = " . json_encode($json) . ";";
}
?>