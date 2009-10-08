// shortcut
function L(x) {
   if (window.console && window.console.log)
     window.console.log(x);
}


function makeWindow(name, user_url, location, photo, iso_code, lat, lon, clubs) {
    var html = '<img class="list-photo" src="' + photo + '" alt="' + name + '">' + 
        '<h3><a href="' + user_url + '">' + name + '</a></h3>' + 
        '<p class="meta"><a href="/' + iso_code + '/" class="nobg">' + 
        '<img src="/static/img/flags/' + iso_code + '.gif"></a> ' + 
        location + '</p>' + 
        '<p class="meta"><a href="#" onclick="zoomOn(' + lat + ', ' + lon + '); return false;">Zoom to point</a></p>';
   if (clubs && clubs.length) {
      html += "<p><strong>" + (clubs.length == 1) ? "Club:" : "Clubs:";
      html += "</strong> ";
      $.each(clubs, function(i, each) {
         html += '<a href="' + each.url + '">' + each.name + '</a><br/>';
      });
      html += "</p>";
   }
     return html;
}
function makeWindow2(username) {
   L("making a window");
   return "<strong>" + username + "</strong>";
}


function makePhotoWindow(name, url, user_url, location, photo, iso_code, lat, lon, description) {
    var html = '<a href="' + url + '"><img class="list-photo" src="' + photo + '" alt="' + name + '"></a>' +
        '<p><strong>Uploaded by<br/><a href="' + user_url + '">' + name + '</a></strong></p>' +
        '<p class="meta"><a href="/' + iso_code + '/" class="nobg">' + 
        '<img src="/static/img/flags/' + iso_code + '.gif"></a> ' + 
        location + '</p>' + 
        '<p class="meta"><a href="#" onclick="zoomOn(' + lat + ', ' + lon + '); return false;">Zoom to point</a></p>';
   if (description)
     html += "<p><em>" + description + "</em></p>";
   return html;
}


function zoomOn(lat, lon) {
    gmap.setCenter(new google.maps.LatLng(lat, lon), 10);
}

function hideNearbyPeople(gmap) {
    gmap.clearOverlays();
}
function showNearbyPeople(gmap) {
   if (typeof nearby_people != "undefined")
     $.each(nearby_people, function() {
        var lat = this[MAP_KEYS['latitude']];
        var lon = this[MAP_KEYS['longitude']];
        var name = this[MAP_KEYS['fullname']];
        var user_url = this[MAP_KEYS['user_url']];
        var location_description = this[MAP_KEYS['location_description']];
        var photo = this[MAP_KEYS['photo_thumbnail_url']];
        var iso_code = this[MAP_KEYS['country_iso_code']];
        var clubs = this[MAP_KEYS['clubs']];
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
    greenIcon.image = "/img/reddot.png";
    greenIcon.iconSize = new google.maps.Size(30,30);
    greenIcon.shadowSize = new google.maps.Size(0,0);
    greenIcon.iconAnchor = new google.maps.Point(18,20);
    greenIcon.infoWindowAnchor = new google.maps.Point(16,0); 
    markerOpts = { icon: greenIcon };
    return markerOpts;
}

function getMarkerOptsThumbnail(thumbnail_url) {
    var greenIcon = new google.maps.Icon(google.maps.DEFAULT_ICON);
    greenIcon.image = thumbnail_url;
    greenIcon.iconSize = new google.maps.Size(32,32);
    greenIcon.shadowSize = new google.maps.Size(56,32);
    greenIcon.iconAnchor = new google.maps.Point(16,32);
    greenIcon.infoWindowAnchor = new google.maps.Point(16,0); 
    markerOpts = { icon: greenIcon };
    return markerOpts;
}

$(function() {
   if (typeof CACHE_CONTROL != "undefined" && CACHE_CONTROL) {
      // the page is cached, need to use AJAX to load what should be
      // dynamic
      $('#nav').load('/_nav.html');
      // 
   }
});