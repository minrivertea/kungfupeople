// shortcut
function L(x) {
   if (window.console && window.console.log)
     window.console.log(x);
}


function makeWindow(name, user_url, location, photo, iso_code, lat, lon, clubs) {
    var html =   
        '<img class="list-photo" src="' + photo + '" alt="' + name + '">' + 
        '<h3><a href="' + user_url + '">' + name + '</a></h3>' + 
        '<p class="meta"><a href="/' + iso_code + '/" class="nobg">' + 
        '<img src="/static/img/flags/' + iso_code + '.gif"></a> ' + 
        location + '</p>' + 
        '<p class="meta"><a href="#" onclick="zoomOn(' + lat + ', ' + lon + '); return false;">Zoom to point</a></p>';
   if (clubs) {
      html += "<p><strong>" + (clubs.length == 1) ? "Club:" : "Clubs:";
      html += "</strong> ";
      $.each(clubs, function(i, each) {
         html += '<a href="' + each.url + '">' + each.name + '</a><br/>';
      });
      html += "</p>";
   }
     return html;
}

function zoomOn(lat, lon) {
    //gmap.closeInfoWindow();
    gmap.setCenter(new google.maps.LatLng(lat, lon), 10);
}

function hideNearbyPeople(gmap) {
    gmap.clearOverlays();
}
function showNearbyPeople(gmap) {
   if (typeof nearby_people != "undefined")
     $.each(nearby_people, function() {
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
           
           try {
              var window = makeWindow(name, user_url, location_description, photo, 
                                      iso_code, lat, lon, clubs
                                      );
           } catch(ex) {
              alert(ex);
           }
           marker.openInfoWindow(window);
        });
     });
};

function getMarkerOpts() {
    var greenIcon = new google.maps.Icon(google.maps.DEFAULT_ICON);
    greenIcon.image = "http://djangopeople.net/static/img/green-bubble.png";
    greenIcon.iconSize = new google.maps.Size(32,32);
    greenIcon.shadowSize = new google.maps.Size(56,32);
    greenIcon.iconAnchor = new google.maps.Point(16,32);
    greenIcon.infoWindowAnchor = new google.maps.Point(16,0); 
    markerOpts = { icon: greenIcon };
    return markerOpts;
}

