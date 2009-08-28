function __not_youtube_video() {
  $('#video-youtube').hide(500);
  $('#video-details:hidden').show(300);
}

var _youtube_video_id_lookup;
var _fetching = false; // custom lock file


function __pre_fetch_video_details() {
  $('.pleasewait:hidden').show();
}

function __post_fetch_video_details() {
  $('.pleasewait:visible').hide();
}

function __fetch_video_details(video_id) {
    _youtube_video_id_lookup = video_id;
    if (_fetching) return;
    _fetching = true;
    $.getJSON('/get_youtube_video_by_id.json', {video_id:video_id}, function(res) {
      if (res.error) {
        alert("Error! " + res.error);
      } else {
        $('#video-details:hidden').show(400);
        $('#embed_src-outer').hide();
        if (res.embed_src) {
          $('#id_embed_src').val(res.embed_src);
          $('#preview-outer:hidden').show();
          $('div.form-field-right', '#preview-outer').html(res.embed_src);
          $('#embed_src-outer').hide();
        }
        if (res.title)
          $('#id_title').val(res.title);
        if (res.description)
          $('#id_description').val(res.description);
        if (res.thumbnail_url)
          $('#id_thumbnail_url').val(res.thumbnail_url);
          
      }
      _fetching = false;
      __post_fetch_video_details();
    });

}

$(function() {
  
  if (!$('#id_youtube_video_id').val() && !$('#id_embed_src').val()) {
    $('#video-details:visible').hide();//fadeTo(0, 0.3);
    $('#video-youtube').append(
      $('<a href="#"></a>').bind('click', function() {
        __not_youtube_video();
        return false;
      }).append($("<span>(No, it's not a YouTube video)</span>"))
    );
  }
  
  function update_by_video_id(video_id) {
    if (!$.trim(video_id).length) return;
    if (_youtube_video_id_lookup && _youtube_video_id_lookup == video_id)
      return;
    __pre_fetch_video_details();
    __fetch_video_details(video_id);
  }
  $('#id_youtube_video_id')
    .bind('keyup', function() {update_by_video_id($(this).val())})
    .bind('change', function() {update_by_video_id($(this).val())});
  
  $('form[method="post"]').bind('submit', function() {
    if ($('#id_youtube_video_id').val() && !$('#id_embed_src').val()) {
      update_by_video_id($('#id_youtube_video_id').val());
      return false;
    }
    if (!$('#id_embed_src').val()) {
      alert("No video code");
      return false;
    }
    if (!$('#id_title').val()) {
      alert("Video title missing");
      return false;
    }    
      
    return true;
    
  });
  
    
});
