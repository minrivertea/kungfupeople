if (typeof LOCATION_BY_IP == "undefined")
  var LOCATION_BY_IP=false;
  
  
$(function() {
   
   
   // When you fill in the club_url, prefill the club name if possible
   $('#id_club_url').change(function() {
      var club_url = $(this).val();
      if ($.trim(club_url)) {
         $.getJSON('/guess-club-name.json', {club_url:club_url}, function(res) {
            if (res && res.club_name) {
               $('#id_club_name').val(res.club_name);
               if (res.readonly)
                 $('#id_club_name').attr('readonly','readonly').attr('disabled','disabled').addClass('readonly');
            }
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
   
});
