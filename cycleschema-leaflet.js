var campBikeCounts
var config = {
    // All polling intervals are all in milliseconds!

    // How often to update the background image showing the bike trails generated by MapServer.
    bikePositionPollingInterval: 500,

    // How often to request an update on bike positions from the backend. This impacts how quickly the theme camps animations will update in response to changes in the position of the bikes.
    bikeStatusPollingInterval: 1000,

    // How often to tick the theme camp and Church of Belligerence animations. One tick = One frame in the animation. Tweak this if the animations seem too fast or too slow.
    campAnimationTickInterval: 128,

    // DO NOT USE
    // campAnimationUseSimpleGIFs: true,

    // Control the position of the map
    map: {
        lat: -32.6592,
        lon: 118.3305,
        zoom: 16,
    },
}

/* Setup The Map */
var map = L.map("map", {
    zoomControl: false,
    attributionControl: false,
    crs: L.CRS.EPSG4326,
}).setView([config.map.lat, config.map.lon], config.map.zoom)

// Disable drag and zoom handlers on the map
map.dragging.disable()
map.touchZoom.disable()
map.doubleClickZoom.disable()
map.scrollWheelZoom.disable()

/* Add Our Basemap Layer: Contains the bike paths */
var wms = L.WMS.overlay("mapserver/wms.php?foo=" + Math.random(), {
    layers: "bikes",
    format: "image/png",
}).addTo(map)

window.setInterval(function() {
    wms.setParams({ url: "mapserver/wms.php?foo=" + Math.random() })
}, config.bikePositionPollingInterval)

/* Add Our Camps To The Map */
var campIconFrames = []
let padToFive = number => (number <= 99999 ? ("0000" + number).slice(-5) : number)

for (let camp of camps) {
    campIconFrames[camp["name"]] = 0

    var icon = new L.DivIcon({
        className: camp["name"],
        iconSize: [camp["icon_width"], camp["icon_height"]],
        iconAnchor: [camp["icon_width"] / 2, camp["icon_height"] / 2],
    })
    L.marker([camp["lat"], camp["lon"]], { icon: icon }).addTo(map)

    $("." + camp["name"]).html(
        '<img src="" width="' + camp["icon_width"] + '" height="' + camp["icon_height"] + '" class="' + camp["name"] + '_0" />'
    )
}

window.setInterval(function() {
    for (let camp of camps) {
        // var oldCamp = JSON.parse(JSON.stringify(camp))

        camp = applyCampAnimationLogic(camp)
        $("." + camp["name"] + " > img").attr("class", camp["name"] + "_" + camp["current_frame"])

        // if (camp !== oldCamp) {
        // console.log(`${camp["name"]} (Bikes = ${campBikeCounts[camp["name"]]}; Frame = ${camp["current_frame"]}; State = ${camp["current_state"]};`)
        // }

        // Abandoned - we'd need to know how long to show a non-looping
        // powering-up/down GIF before we showed the powered-on/down equivalent
        /*if (config.campAnimationUseSimpleGIFs == false) {
      if (campBikeCounts !== undefined) {
        camp = applyCampAnimationLogic(camp)
        $("." + camp["name"] + " > img").attr("class", camp["name"] + "_" + camp["current_frame"]);
      }

    } else {
      // camp = applySimpleCampAnimationLogic(camp)
      camp = applyCampAnimationLogic(camp)
      console.log(camp["name"] + ": " + camp["current_state"])
      // $("." + camp["name"] + " > img").attr("src", "/mapserver/icons/" + camp["base_url"] + ".gif").attr("class", "");

      $("." + camp["name"] + " > img").attr("src", "/mapserver/icons/" + camp["base_url"] + "_" + camp["current_state"].toLowerCase() + ".gif").attr("class", "");
    }*/
    }
}, config.campAnimationTickInterval)

/* Poll The Backend For Updated Bike Location Data */
window.setInterval(function() {
    $.ajax({
        url: "mapserver/bike-counts.json",
        data: { foo: Math.random() },
        success: function(data, textStatus) {
            campBikeCounts = data
        },
    })
}, config.bikeStatusPollingInterval)