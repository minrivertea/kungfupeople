$(function() {
   // When you fill in the club_url, prefill the club name if possible
   $('#id_club_url').change(function() {
      var club_url = $(this).val();
      if ($.trim(club_url)) {
         $.getJSON('/guess-club-name.json', {club_url:club_url}, function(res) {
            if (res) {
              if (res.club_name) {
                 $('#id_club_name').val(res.club_name);
                 if (res.readonly)
                   $('#id_club_name').attr('readonly','readonly').attr('disabled','disabled').addClass('readonly');
              } else if (res.error) {
                 alert(res.error);
              }
            }
         });
      }
   });
});