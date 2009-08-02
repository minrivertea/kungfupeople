function __show_zoom_content(result) {
   var container = $('#zoom-content-outer');
   // clear any "please wait" signs
   $('*', container).remove();
   var subcontainer;
   
   var installations = [{data:result.clubs && result.clubs || [],
                         id:'clubs',
                         title:"Clubs"},
                        {data:result.styles && result.styles || [],
                         id:'style',
                         title:"Style"},
                        {data:result.people && result.people || [],
                         id:'people',
                         title:"People"},
                        {data:result.photos && result.photos || [],
                         id:'photos',
                         title:"Photos"},
                        {data:result.diary_entries && result.diary_entries || [],
                         id:'diary_entries',
                         title:"Diary entries"}//,
                        ];
   
   
   var link;
   $.each(installations, function(i, installation) {
      $('#zoomed-content__' + installation.id, container).remove();
      subcontainer = null;
      $.each(installation.data, function (j, item) {
         if (!subcontainer)
           subcontainer = $('<div></div>')
             .attr('id', 'zoomed-content__' + installation.id)
               .addClass('zoomed-content')
                 .append($('<h3>' + installation.title + '</h3>'));
         
         if (installation.id=='people') {
            link = $('<a></a>')
              .attr('href', item.url)
                .attr('title', item.fullname);
            link.append($('<img>').attr('src',item.thumbnail_url));
            subcontainer.append(link);
            
            var point = new google.maps.LatLng(item.lat, item.lng);
            var marker = new google.maps.Marker(point, getMarkerOptsThumbnail(item.marker_thumbnail_url));
            gmap.addOverlay(marker);
            google.maps.Event.addListener(marker, 'click', function() {
               try {
                  var window = makeWindow(item.fullname, item.url, item.location_description,
                                          item.thumbnail_url, item.iso_code, item.lat, item.lng,
                                          item.clubs);
               } catch(ex) {
                  alert(ex);
               }
               marker.openInfoWindow(window);
            });
            
            

         } else if (installation.id=='photos') {
            subcontainer.append($('<a></a>')
                                .attr('href', item.url)
                                .append($('<img>').attr('src', item.thumbnail_url)));
            var point = new google.maps.LatLng(item.lat, item.lng);
            var marker = new google.maps.Marker(point, getMarkerOptsThumbnail(item.marker_thumbnail_url));
            gmap.addOverlay(marker);
            google.maps.Event.addListener(marker, 'click', function() {
               try {
                  var window = makePhotoWindow(item.fullname, item.url, item.location_description,
                                               item.thumbnail_url, item.iso_code, item.lat, item.lng,
                                               item.description);
               } catch(ex) {
                  alert(ex);
               }
               marker.openInfoWindow(window);
            });            
            //var point = new google.maps.LatLng(item.lat, item.lng);
            //var marker = new google.maps.Marker(point, getMarkerOpts());
            //gmap.addOverlay(marker);

         } else {
            if (installation.id=='diary_entries')
              subcontainer.append($('<a></a>').attr('href', item.url).attr('title', item.title).text(item.title));
            else
              subcontainer.append($('<a></a>').attr('href', item.url).attr('title', item.name).text(item.name));
            subcontainer.append($('<br>')); // need to test in IE
         }
      });
      
      if (subcontainer) container.append(subcontainer);

   });
   
   if (result.countries) {
      subcontainer = null;
      $.each(result.countries, function(j, item) {
         if (!subcontainer)
           subcontainer = $('<div></div>')
             .attr('id', 'zoomed-content__countries')
               .addClass('zoomed-content')
                 .append($('<h3>Countries</h3>'));
         subcontainer.append($('<a></a>').attr('href', item.url).attr('title', item.title).text(item.title));
         subcontainer.append($('<br>')); // need to test in IE
         
      });
      if (subcontainer) container.append(subcontainer);
   }
   
   
}

function __show_no_zoom_content() {
   $("#zoom-content-outer").html("<em>Nothing here :(</em>");
}


function GoogleMapsCallback(gmap) {
   
   
   GEvent.addListener(gmap, "zoomend", function(oldLevel, newLevel) {
      
      if (newLevel < 4) {
         $('#zoom-content-outer').append($("<h3 align=\"center\">Zoom in a bit more please</h3>"));
         return ;
      }
      else
        $('#zoom-content-outer').append($("<p>Please wait...</p>"));
      
      var latlngbounds = gmap.getBounds();
      var northeast = latlngbounds.getNorthEast();
      var southwest = latlngbounds.getSouthWest();
      var left = northeast.lat();
      var lower = northeast.lng();
      var right = southwest.lat();
      var upper = southwest.lng();

      $.getJSON('/zoom-content.json',{left:left, upper:upper, right:right, lower:lower}, function(result) {
         if (result) {
            if (result.error) alert(result.error);
            else {
               try {
                  __show_zoom_content(result);
               } catch(ex) {
                  alert(ex);
               }
            }
         } else {
            __show_no_zoom_content();
         }
         
	 
      });
      
   });
   
}