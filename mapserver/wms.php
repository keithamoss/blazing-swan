<?php
$execQuery = "mapserv -nh \"QUERY_STRING=map=./bikes.map&" . http_build_query($_GET) . "\"";
$output = shell_exec($execQuery);
echo $output;
?>