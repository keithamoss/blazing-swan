<?php
// require_once "config.php";
// echo "var camps = " . json_encode($camps) . ";";

echo "var camps = " . file_get_contents("mapserver/camps.json") . ";";
?>