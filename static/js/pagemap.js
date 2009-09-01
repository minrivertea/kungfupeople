
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
         gmap.removeControl(map_control);
	 gmap.removeControl(map_type_control);
	 gmap.removeControl(shrinkControl);
	 // Back to original center:
	 var point = new google.maps.LatLng(PAGE_LATITUDE, PAGE_LONGITUDE);
	 var marker = new google.maps.Marker(point, getMarkerOpts());
	 gmap.addOverlay(marker);
	 
	 $('#gmap').animate({
	    height: '7em'
	 }, 500, 'swing', function() {
	    gmap.checkResize();
	    gmap.setCenter(point, ZOOM);
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

var shrinkControl;
function onMapClicked() {
   shrinkControl = new ShrinkControl();
   $('#gmap').css({'cursor': ''}).attr('title', '');
   $('#gmap').animate({
      height: '25em'
   }, 500, 'swing', function() {
      gmap.checkResize();
      gmap.enableDragging();
      // Need to recreate LargeMapControl to work around a bug
      gmap.addControl(map_control);
      gmap.addControl(map_type_control);
      gmap.addControl(shrinkControl);
      if (typeof PEOPLE != 'undefined')
        show_people(PEOPLE);
      // Unbind event so user can actually interact with map
      $('#gmap').unbind('click', onMapClicked);
   });
   $('.right-box-top').animate({opacity: 1.0});
}

function GoogleMapsCallback(gmap) {
   gmap.removeControl(map_control);
   gmap.removeControl(map_type_control);
   hide_people();
   show_person(PERSON);
     
   /* Map enlarges and becomes active when you click on it */
   $('#gmap')
     .css({'cursor': 'pointer', 'opacity': 1.0})
       .attr('title', 'Activate larger map');
   
   $('.right-box-top')
     .css({'cursor': 'pointer', 'opacity': 1.0})
       .attr('title', 'Activate larger map');
   
   gmap.disableDragging();
   
   $('#gmap').click(onMapClicked);

};