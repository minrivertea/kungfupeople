google.load('maps', '2',{'other_params':'sensor=false'});

var gmap;
google.setOnLoadCallback(function() {
    gmap = new google.maps.Map2(document.getElementById('gmap'));
    gmap.addControl(new google.maps.LargeMapControl3D());
    gmap.addControl(new google.maps.MapTypeControl());
    // We have to render the map first or the bounds calculations will fail
    gmap.setCenter(new google.maps.LatLng(0, 0));
    var bounds = new google.maps.LatLngBounds();
    
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
        var marker = new google.maps.Marker(point, getMarkerOpts());
        bounds.extend(point);
        gmap.addOverlay(marker);
        // Hook up the marker click event
        google.maps.Event.addListener(marker, 'click', function() {
            marker.openInfoWindow(makeWindow(
                name, username, location_description, photo, iso_code, 
                lat, lon
            ));
        });
    });
    gmap.setZoom(Math.min(gmap.getBoundsZoomLevel(bounds) - 1, 8));
    gmap.setCenter(bounds.getCenter());
});
