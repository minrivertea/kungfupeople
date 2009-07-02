google.load('maps', '2',{'other_params':'sensor=false'});

var gmap; 

google.setOnLoadCallback(function() {
   if (!document.getElementById('gmap')) return ;
   if (OFFLINE_MODE) return;
   
   function ShrinkControl() {}
   ShrinkControl.prototype = new GControl();
   ShrinkControl.prototype.initialize = function(gmap) {
      var shrinkButton = document.createElement('div');
      shrinkButton.innerHTML = 'Shrink map';
      this.setButtonStyle_(shrinkButton);
      google.maps.Event.addDomListener(shrinkButton, "click", function() {
	 $('#gmap').css({'cursor': 'pointer'}).attr(
						    'title', 'Activate larger map'
						    );
	 hideNearbyPeople(gmap);
	 gmap.removeControl(largeMapControl);
	 gmap.removeControl(mapTypeControl);
	 gmap.removeControl(shrinkControl);
	 // Back to original center:
	 var point = new google.maps.LatLng(
					    person_latitude, person_longitude
					    );
	 var marker = new google.maps.Marker(point, getMarkerOpts());
	 gmap.addOverlay(marker);
	 
	 $('#gmap').animate({
	    height: '7em',
	      opacity: 1.0
	 }, 500, 'swing', function() {
	    gmap.checkResize();
	    gmap.setCenter(point, 12);
	    gmap.disableDragging();
	    $('#gmap').click(onMapClicked);
	 });
      });
      gmap.getContainer().appendChild(shrinkButton);
      return shrinkButton;
   }
   ShrinkControl.prototype.getDefaultPosition = function() {
      return new GControlPosition(G_ANCHOR_BOTTOM_LEFT, new GSize(70, 7));
   }
   
   // Sets the proper CSS for the given button element.
   ShrinkControl.prototype.setButtonStyle_ = function(button) {
      button.style.color = "black";
      button.style.backgroundColor = "white";
      button.style.font = "12px Arial";
      button.style.border = "1px solid black";
      button.style.padding = "2px";
      button.style.marginBottom = "3px";
      button.style.textAlign = "center";
      button.style.width = "6em";
      button.style.cursor = "pointer";
   }
   
   var largeMapControl = new google.maps.LargeMapControl();
   var mapTypeControl = new google.maps.MapTypeControl();
   var shrinkControl = new ShrinkControl();
   
   gmap = new google.maps.Map2(document.getElementById('gmap'));
    
   /* Map enlarges and becomes active when you click on it */
   $('#gmap')
     .css({'cursor': 'pointer', 'opacity': 1.0})
       .attr('title', 'Activate larger map');
   
   $('.right-box-top')
     .css({'cursor': 'pointer', 'opacity': 1.0})
       .attr('title', 'Activate larger map');
   
   gmap.disableDragging();
   function onMapClicked() {
      $('#gmap').css({'cursor': ''}).attr('title', '');
      $('#gmap').animate({
	 height: '25em',
	   opacity: 1.0
      }, 500, 'swing', function() {
	 gmap.checkResize();
	 gmap.enableDragging();
	 // Need to recreate LargeMapControl to work around a bug
	 largeMapControl = new google.maps.LargeMapControl();
	 gmap.addControl(largeMapControl);
	 gmap.addControl(mapTypeControl);
	 gmap.addControl(shrinkControl);
	 showNearbyPeople(gmap);
	 // Unbind event so user can actually interact with map
	 $('#gmap').unbind('click', onMapClicked);
      });
      $('.right-box-top').animate({opacity: 1.0});
   }
   $('#gmap').click(onMapClicked);
   
   if (typeof PAGE_LATITUDE=='undefined') {L('variable PAGE_LATITUDE not set'); return}
   if (typeof PAGE_LONGITUDE=='undefined') {L('variable PAGE_LONGITUDE not set'); return}
   
   var point = new google.maps.LatLng(PAGE_LATITUDE, PAGE_LONGITUDE);
   gmap.setCenter(point, 9);
   var marker = new google.maps.Marker(point, getMarkerOpts());
   gmap.addOverlay(marker);
});