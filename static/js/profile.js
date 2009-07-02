$(function() {
    
    if ($('#uploadNewPhoto').length && $('div.header img.main').length) {
        var href = $('a#uploadNewPhoto').attr('href');
        $('#uploadNewPhoto').remove();
        var upload = $('<a href="' + href + '">(replace)</a>').appendTo(
            document.body
        );
        var img = $('div.header img.main');
        upload.css({
            'font-size': '10px',
            'text-decoration': 'none',
            'color': 'white',
            'padding': '0px 2px 0px 2px',
            'background-color': 'black',
            'position': 'absolute',
            'top': img.offset().top + img.height() - upload.height() - 1,
            'left': img.offset().left + 4,
            'visibility': 'hidden'
        });
        img.mouseover(function() {
            upload.css('visibility', 'visible');
        });
        upload.mouseover(function() {
            upload.css('visibility', 'visible');
        });
        img.mouseout(function() {
            upload.css('visibility', 'hidden');
        });
    }
});
