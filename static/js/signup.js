jQuery.fn.yellowFade = function() {
    return this.css({
        'backgroundColor': 'yellow'
    }).animate({
        'backgroundColor': 'white'
    }, 1500);
}

google.load('maps', '3');

var INITIAL_LAT = 43.834526782236814;
var INITIAL_LON = -37.265625;

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
   $('.text', '#loading-inner:hidden').text('Fetching name by location...');
   $('#loading-inner:hidden').show();
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
            if ($('#id_location_description').val() != name) {
                $('#id_location_description').val(name);
                $('#id_location_description').parent().yellowFade();
            }
            $('#id_country').val(iso_code).change();
            // Update region field, if necessary
            if (hasRegions(countryName) && place.adminCode1) {
                $('#id_region').val(place.adminCode1);
            } else {
                $('#id_region').val('');
            }
        }
       $('#loading-inner:visible').hide();
    });
}

function hasRegions(country_name) {
    return $('select#id_region optgroup[label="' + country_name + '"]').length;
}


var gmap;
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
    var lookupTimer = false;
    
    google.maps.Event.addListener(gmap, "move", function() {
        window.center = gmap.getCenter();
        if (lookupTimer) {
            clearTimeout(lookupTimer);
        }
        lookupTimer = setTimeout(reverseGeocode, 1200);
        $('#id_latitude').val(center.lat());
        $('#id_longitude').val(center.lng());
    });
    google.maps.Event.addDomListener(document.getElementById('crosshair'),
        'dblclick', function() {
            gmap.zoomIn();
        }
    );
    
    /* The first time the map is hovered, scroll the page */
    $('#gmap').one('click', function() {
        $('html,body').animate({scrollTop: $('#gmap').offset().top}, 500);
    });
    
    var point;
    /* If latitude and longitude are populated, center there */
    if ($('#id_latitude').val() && $('#id_longitude').val()) {
        point = new google.maps.LatLng(
            $('#id_latitude').val(),
            $('#id_longitude').val()
        );
        gmap.setCenter(point, 9);
    } else {
        gmap.setCenter(new google.maps.LatLng(INITIAL_LAT, INITIAL_LON), 3);
    }
   
   
   // When you fill in the club_url, prefill the club name if possible
   $('#id_club_url').change(function() {
      var club_url = $(this).val();
      if ($.trim(club_url)) {
         jQuery.getJSON('/guess-club-name.json', {club_url:club_url}, function(res) {
            if (res && res.club_name)
              jQuery('#id_club_name').val(res.club_name);
         });
      }
   });
   
   // When you enter an email address with no username set,
   // guess a suitable username based on the email
   $('#id_email').change(function() {
      if ($(this).val() && !$('#id_username').val())
        $.getJSON('/guess-username.json', 
                  {email:$(this).val(),
                     first_name:$('#id_first_name').val(),
                     last_name:$('#id_last_name').val()
                  }, function(res) {
                     if (res && res.username)
                       $('#id_username').val(res.username);
                  }
                  );
      
   });
   
   
   $('#loading-inner').hide();
   
});