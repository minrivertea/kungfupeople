google.load('maps', '2',{'other_params':'sensor=false'});

function show_person(person) {
   var lat = person[MAP_KEYS['latitude']];
   var lon = person[MAP_KEYS['longitude']];
   var username = person[MAP_KEYS['username']];
   var point = new google.maps.LatLng(lat, lon);
   var marker = new google.maps.Marker(point, getMarkerOpts());
   gmap.addOverlay(marker);
   // Hook up the marker click event
   google.maps.Event.addListener(marker, 'click', function() {
      $.get('/' + username +'/_user-info-map.html', function (result) {
         marker.openInfoWindow(result);
      });
   });
}
function show_people(people) {
    // Plot the people as markers
    $.each(people, function() {
       show_person(this);
    });
}
function hide_people() {
   gmap.clearOverlays();
}

var gmap;
var bounds;
var map_control;
var map_type_control;
google.setOnLoadCallback(function() {
   
   gmap = new google.maps.Map2(document.getElementById('gmap'));
    
   map_control = new google.maps.LargeMapControl3D();
   map_type_control = new google.maps.MapTypeControl();
   gmap.addControl(map_control);
   gmap.addControl(map_type_control);

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
      if (typeof PAGE_LATITUDE == 'undefined' && typeof PAGE_LONGITUDE == 'undefined')
	//var latlng = new google.maps.LatLng(19.97335, -15.8203);
        var latlng = new google.maps.LatLng(27.97335, -15.8203);
      else
	var latlng = new google.maps.LatLng(PAGE_LATITUDE, PAGE_LONGITUDE);
      if (typeof ZOOM == 'undefined')
        gmap.setCenter(latlng, 2);
      else
        gmap.setCenter(latlng, ZOOM);
   }
   
   if (typeof PEOPLE != "undefined")
     show_people(PEOPLE);
   
   if (typeof GoogleMapsCallback != "undefined") {
     GoogleMapsCallback(gmap);
   }
      
});
