google.load('maps', '3');

var gmap;
google.setOnLoadCallback(function() {
    var latlng = new google.maps.LatLng(19.97335, -15.8203);
    gmap = new google.maps.Map2(document.getElementById('gmap'));
    gmap.setCenter(latlng, 2);
    
    //gmap.addControl(new google.maps.LargeMapControl());
    gmap.addControl(new google.maps.LargeMapControl3D());
    gmap.addControl(new google.maps.MapTypeControl());

    
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
        gmap.addOverlay(marker);
        // Hook up the marker click event
        google.maps.Event.addListener(marker, 'click', function() {
            marker.openInfoWindow(makeWindow(
                name, username, location_description, photo, iso_code, 
                lat, lon
            ));
        });
    });
});
