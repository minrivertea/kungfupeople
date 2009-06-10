google.load('maps', '2',{"other_params":"sensor=false"});

var gmap;
google.setOnLoadCallback(function() {
    gmap = new google.maps.Map2(document.getElementById('gmap'));
    gmap.addControl(new google.maps.LargeMapControl());
    gmap.addControl(new google.maps.MapTypeControl());
    // Figure out map settings based on country bounds
    // We have to render the map first or the bounds calculations will fail
    gmap.setCenter(new google.maps.LatLng(bbox_north, bbox_west));
    var bounds = new google.maps.LatLngBounds();
    bounds.extend(new google.maps.LatLng(bbox_north, bbox_west));
    bounds.extend(new google.maps.LatLng(bbox_south, bbox_east));
    gmap.setZoom(gmap.getBoundsZoomLevel(bounds));
    gmap.setCenter(bounds.getCenter());
    
    // Plot the people as markers
    $.each(people, function() {
        var lat = this[0];
        var lon = this[1];
        var name = this[2];
        var username = this[3];
        var location_description = this[4];
        var photo = this[5];
        var iso_code = this[6];
        var point = new google.maps.LatLng(lat, lon);
        bounds.extend(point);
        var marker = new google.maps.Marker(point, getMarkerOpts());
        gmap.addOverlay(marker);
        // Hook up the marker click event
        google.maps.Event.addListener(marker, 'click', function() {
            marker.openInfoWindow(makeWindow(
                name, username, location_description, photo, iso_code, 
                lat, lon
            ));
        });
    });
    // Re-plot, just in case someone was outside the original bounds (e.g. a 
    // US resident of Hawaii)
    gmap.setCenter(bounds.getCenter());

});
