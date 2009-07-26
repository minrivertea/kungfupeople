google.load('maps', '2',{'other_params':'sensor=false'});

var gmap;
var bounds;
google.setOnLoadCallback(function() {
   
    gmap = new google.maps.Map2(document.getElementById('gmap'));
    
    //gmap.addControl(new google.maps.LargeMapControl());
    gmap.addControl(new google.maps.LargeMapControl3D());
    gmap.addControl(new google.maps.MapTypeControl());

   if (typeof bbox_north != "undefined") {
      // Figure out map settings based on country bounds
      // We have to render the map first or the bounds calculations will fail
      gmap.setCenter(new google.maps.LatLng(bbox_north, bbox_west));
      bounds = new google.maps.LatLngBounds();
      bounds.extend(new google.maps.LatLng(bbox_north, bbox_west));
      bounds.extend(new google.maps.LatLng(bbox_south, bbox_east));
      gmap.setZoom(gmap.getBoundsZoomLevel(bounds));
      gmap.setCenter(bounds.getCenter());
   } else {
      var latlng = new google.maps.LatLng(19.97335, -15.8203);
      gmap.setCenter(latlng, 2);
   }
   
    // Plot the people as markers
    $.each(people, function() {
        var lat = this[NEARBY_PERSON_KEYS['latitude']];
        var lon = this[NEARBY_PERSON_KEYS['longitude']];
        var name = this[NEARBY_PERSON_KEYS['fullname']];
        var user_url = this[NEARBY_PERSON_KEYS['user_url']];
        var location_description = this[NEARBY_PERSON_KEYS['location_description']];
        var photo = this[NEARBY_PERSON_KEYS['photo_thumbnail_url']];
        var iso_code = this[NEARBY_PERSON_KEYS['country_iso_code']];
        var clubs = this[NEARBY_PERSON_KEYS['clubs']];
        var point = new google.maps.LatLng(lat, lon);
        var marker = new google.maps.Marker(point, getMarkerOpts());
        gmap.addOverlay(marker);
        // Hook up the marker click event
        google.maps.Event.addListener(marker, 'click', function() {
            marker.openInfoWindow(makeWindow(
                name, user_url, location_description, photo, iso_code, 
                lat, lon, clubs
            ));
        });
    });
   
   
   if (typeof GoogleMapsCallback != "undefined")
     GoogleMapsCallback(gmap);
      
});
