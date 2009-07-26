function GoogleMapsCallback(gmap) {
   
   
   GEvent.addListener(gmap, "zoomend", function(oldLevel, newLevel) {
      
      if (newLevel < 4) {
         $('#zoom-content-outer').append($("<h3 align=\"center\">Zoom in a bit more please</h3>"));
         return ;
      }
      else
        $('#zoom-content-outer').text("Please wait...");
      
      var latlngbounds = gmap.getBounds();
      var northeast = latlngbounds.getNorthEast();
      var southwest = latlngbounds.getSouthWest();
      var left = northeast.lat();
      var lower = northeast.lng();
      var right = southwest.lat();
      var upper = southwest.lng();
      
      $('#zoom-content-outer').load('/zoom-content/', 
                                    {left:left, upper:upper, right:right, lower:lower}
                                         );
      
      
   });
   
}