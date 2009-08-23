jQuery.fn.yellowFade = function() {
    return this.css({
        'backgroundColor': 'yellow'
    }).animate({
        'backgroundColor': 'white'
    }, 1500);
}

google.load('maps', '2',{'other_params':'sensor=false'});

if (typeof INITIAL_LAT == "undefined")
  var INITIAL_LAT = 43.834526782236814;
if (typeof INITIAL_LON == "undefined")
  var INITIAL_LON = -37.265625;
if (typeof INITIAL_ZOOM == "undefined")
  var INITIAL_ZOOM = 3;
function __zoom_in(extra) {
   if (!extra) extra=0;
   gmap.setZoom(gmap.getZoom()+2+extra);
}
function __zoom_out(extra) {
   if (!extra) extra=0;
   gmap.setZoom(gmap.getZoom()-2-extra);
}

function __reversed_geocode(name, countryName, iso_code, region) {
   
            if ($('#id_location_description').val() != name) {
                $('#id_location_description').val(name);
                $('#id_location_description').parent().yellowFade();
	       
	       if (marker) {

		  marker_html = name+"<br>"+countryName+"<br>";
                  if (LOCATION_BY_IP)
                    marker_html += "(<font size=\"-1\"><strong>note:</strong> you can correct this in your profile afterwards)</font><br>";
                  marker_html += "<br><font size=\"-1\">zoom ";
		  if (gmap.getZoom() < 14)
		    marker_html += "<a href=\"#\" onclick=\"__zoom_in();return false\">in</a> ";
		  if (gmap.getZoom() > 2)
		    marker_html += "<a href=\"#\" onclick=\"__zoom_out();return false\">out</a>";
		  marker_html += "</font>"
		  marker.openInfoWindowHtml(marker_html);
		  
		  if (gmap.getZoom() >= 2)
		    gmap.setCenter(marker.getLatLng(), gmap.getZoom()+3);
		  
		  if (!($('#id_club_url').val() && $('#id_club_name').val())) {
		     __suggest_club_by_location();
		  }
		  
	       }
	       
            }
	   
            $('#id_country').val(iso_code).change();
            // Update region field, if necessary
            if (region)
     $('#id_region').val('');
}

function reverseGeocode() {
    var lon = $('#id_longitude').val();
    var lat = $('#id_latitude').val();
    // Don't geocode if we're still at the starting point
    if (!lon || !lat || (
            Math.abs(lat - INITIAL_LAT) < 0.01 &&
            Math.abs(lon - INITIAL_LON) < 0.01)) {
        return;
    }
   
    var url = 'http://ws.geonames.org/findNearbyPlaceNameJSON?'
    url += 'lat=' + lat + '&lng=' + lon + '&callback=?';
    jQuery.getJSON(url, function(json) {
        if (typeof json.geonames != 'undefined' && json.geonames.length > 0) {
            // We got results
            var place = json.geonames[0];
            var iso_code = place.countryCode;
            var countryName = place.countryName;
            var adminName1 = place.adminName1;
            var name = place.name;
            if (adminName1 && adminName1.toLowerCase() != name.toLowerCase()) {
                name += ', ' + adminName1;
            }
           var region='';
           if (hasRegions(countryName) && place.adminCode1) 
             region = place.adminCode1;
           
           __reversed_geocode(name, countryName, iso_code, region);
           

        }
       
    });
   return true;
}

var _club_suggestions = {};
function suggest_club(id) {
   if (id) {
      $('#club-suggestions-tip:visible').hide();
      $('#id_club_name').val(_club_suggestions[id][0]);
      $('#id_club_url').val(_club_suggestions[id][1]);
   }
   //if ($('#id_club_name').data("qtip")) $('#id_club_name').qtip("destroy");
   $('#id_club_name').qtip("destroy");
}

function __suggest_club_by_location() {
   var params = {
      latitude: $('#id_latitude').val(),
      longitude: $('#id_longitude').val(),
      country: $('#id_country').val(),
      location_description: $('#id_location_description').val()
   };
                                
   $.getJSON('/find-clubs-by-location.json', params, function(result) {
      if (result.error) { alert(result.error); return; }
      
      if (!result.length) return;
      var html = "<p id=\"club-suggestions-tip\"><strong>Let me guess! Is it";
      if (result.length==1)
        html += "...:";
      else
        html += " one of these:";
      html += "</strong><br/>";
      $.each(result, function(i, each) {
         html += each.name;
         html += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
         _club_suggestions[each.id] = [each.name, each.url];
         html += " <a href=\"#\" onclick=\"suggest_club("+ each.id +"); return false\">yes</a>";
         html += " <a href=\"#\" onclick=\"suggest_club(false); return false\">no</a>";
         html += "<br/>";
      });
      html += "</p>";
      
      if ($('#id_club_name').data("qtip"))
        $('#id_club_name').qtip("destroy");
      
      $('#id_club_name').qtip({
         content: html,
           position: {
              corner : {
                 tooltip: "bottomLeft",
                   target: "topRight"
              }
           },
         style: {
            border: {
               width: 3,
                 radius: 10
            },
            padding: 8,
              tip: true,
              name: "cream"
         },
         show: {
            when: false, // Don't specify a show event
              ready: true // Show the tooltip when ready
         },
         hide: false // Don't specify a hide event
      });
        
   });
}

function hasRegions(country_name) {
    return $('select#id_region optgroup[label="' + country_name + '"]').length;
}

function __on_dragend(delay_seconds) {
   point = marker.getLatLng();
   
   var lat = point.lat();
   var lng = point.lng();
   $('#id_latitude').val(lat);
   $('#id_longitude').val(lng);

   // Don't geocode if we're still at the starting point
   if (!lng || !lat || (Math.abs(lat - INITIAL_LAT) < 0.01 &&
			Math.abs(lng - INITIAL_LON) < 0.01)) {
      marker.openInfoWindowHtml(marker_html);
      return;
   }
   
   marker_html = '<img src="/static/img/loading.gif" width="16" height="16" alt="Please wait..."> '+
                 "Please wait...<br>Fetching location name";
   marker.openInfoWindowHtml(marker_html);

   if (delay_seconds) {
      if (lookupTimer)
        clearTimeout(lookupTimer);
      lookupTimer = setTimeout(reverseGeocode, delay_seconds*1000);
   } else {
      reverseGeocode();
   }
}

function __create_marker(point) {
   marker = new GMarker(point, {draggable:true});
   
   GEvent.addListener(marker, "dragstart", function() {
      gmap.closeInfoWindow();
   });
   
   GEvent.addListener(marker, "dragend", function() {
      __on_dragend(1);
   });

   gmap.addOverlay(marker);
   
}

var zoom_level;
var point;
var marker;
var marker_html;
var gmap;
var lookupTimer = false;

function __iso_code_to_country_name(iso_code) {
   var country_name = iso_code;
   $('option', '#id_country').each(function(i, e) {
      if (e.value==iso_code) country_name = $(e).text();
   });
   return country_name;
}

google.setOnLoadCallback(function() {

    // Set up the select country thing to show flags    
    $('select#id_country').change(function() {
        $(this).parent().find('span.flag').remove();
        var iso_code = $(this).val().toLowerCase();
        if (!iso_code) {
            return;
        }
        $('<span class="flag iso-' + iso_code + '"></span>').insertAfter(this);
    }).change();
    
    // Region select field is shown only if a country with regions is selected
    $('select#id_country').change(function() {
        var selected_text = $(
            'select#id_country option[value="' + $(this).val() + '"]'
        ).text();
        if (hasRegions(selected_text)) {
            $('select#id_region').parent().show();
        } else {
            $('select#id_region').parent().hide();
            $('#id_region').val('');
        }
    }).change();
    
    $('select#id_region').parent().hide();
    // Latitude and longitude should be invisible too
    $('input#id_latitude').parent().hide();
    $('input#id_longitude').parent().hide();
    
    gmap = new google.maps.Map2(document.getElementById('gmap'));
    gmap.addControl(new google.maps.LargeMapControl3D());
    gmap.addControl(new google.maps.MapTypeControl());    
    
   
    // If latitude and longitude are populated, center there 
    if ($('#id_latitude').val() && $('#id_longitude').val()) {
        point = new google.maps.LatLng(
            $('#id_latitude').val(),
            $('#id_longitude').val()
        );
       __create_marker(point);
       if (LOCATION_BY_IP) {
          zoom_level = 5;
          marker_html = "<strong>Drag the marker to where you train</strong><br>";
          marker_html += "Currently at: " + $('#id_location_description').val();
          marker_html += "<br>" + __iso_code_to_country_name($('#id_country').val());
          marker_html += "<br><br><font size=\"-1\">zoom ";
          marker_html += "<a href=\"#\" onclick=\"__zoom_in(3);return false\">in</a> ";
          marker_html += "<a href=\"#\" onclick=\"__zoom_out();return false\">out</a>";
          marker_html += "</font>"
          
          marker.openInfoWindowHtml(marker_html);
          
       } else {
          zoom_level = 8;
       }
       
    } else {
       point = new google.maps.LatLng(INITIAL_LAT, INITIAL_LON);
       zoom_level = INITIAL_ZOOM;
    }
   
   gmap.setCenter(point, zoom_level);
   
   
   if (!marker) {
      $('html,body').animate({scrollTop: $('#gmap').offset().top}, 500);
      if (!point)
	point = gmap.getCenter();
      __create_marker(point);
      marker_html = "Drag the marker to where you train";
      marker.openInfoWindowHtml(marker_html);
   }      
   
});
