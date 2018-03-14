<?php
$camps = [[
  "icon_name" => "camp1",
  "base_url" => "camp1/campfire_",
  "icon_width" => 64,
  "icon_height" => 64,
  # Test Case 1
  # "lon" => 118.329704,
  # "lat" => -32.660247,
  # Test Case 2
  "lon" => 118.332082,
  "lat" => -32.657582,
  # Test Case 3
  # "lon" => 118.330937,
  # "lat" => -32.657042,
  "current_frame" => 0,
  "current_state" => "POWERED_DOWN",
  "states" => [
      "powered_off" => [
          "frame_start" => 0,
      ],
      "powering_up" => [
          "frame_start" => 1,
          "frame_end" => 60,
      ],
      "powered_on" => [
          "frame_start" => 61,
          "frame_end" => 104,
      ],
      "powering_down" => [
          "frame_start" => 105,
          "frame_end" => 149,
      ]
  ],
]];
?>