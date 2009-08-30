# python
from string import Template
from urlparse import urlparse
from cgi import parse_qs

from gdata.service import RequestError
import gdata.youtube
import gdata.youtube.service

yt_service = gdata.youtube.service.YouTubeService()

        
        
def PrintEntryDetails(entry):
    print 'Video title: %s' % entry.media.title.text
    print 'Video published on: %s ' % entry.published.text
    print 'Video description: %s' % entry.media.description.text
    print 'Video category: %s' % entry.media.category[0].text
    print 'Video tags: %s' % entry.media.keywords.text
    print 'Video watch page: %s' % entry.media.player.url
    print 'Video flash player URL: %s' % entry.GetSwfUrl()
    print 'Video duration: %s' % entry.media.duration.seconds
    
    # non entry.media attributes
    if entry.geo:
        print 'Video geo location: %s' % entry.geo.location()
    print 'Video view count: %s' % entry.statistics.view_count
    print 'Video rating: %s' % entry.rating.average
    
    # show alternate formats
    for alternate_format in entry.media.content:
        if 'isDefault' not in alternate_format.extension_attributes:
            print 'Alternate format: %s | url: %s ' % (alternate_format.type,
                                                 alternate_format.url)

    # show thumbnails
    for thumbnail in entry.media.thumbnail:
        print 'Thumbnail url: %s' % thumbnail.url
        
        

class YouTubeVideoError(Exception):
    pass

def video_url_or_id(url_or_id):
    """return the ID.
    If the parameter 'url_or_id' is a URL fish out the video ID out of it
    """
    def url2id(url):
        if '/v/' in url:
            return url.split('/v/')[1].split('&')[0]
        else:
            qs = urlparse(url)[4]
            return parse_qs(qs)['v'][0]
        
    if url_or_id.startswith('http'):
        try:
            return url2id(url_or_id)
        except KeyError:
            raise YouTubeVideoError("No parameter called 'v'")
        except IndexError:
            raise YouTubeVideoError("Parameter 'v' non existant")
    else:
        return url_or_id
    

def get_youtube_video_by_id(url_or_id):
    video_id = video_url_or_id(url_or_id)
        
    title = embed_src = description = None
    
    try:
        entry = yt_service.GetYouTubeVideoEntry(video_id=video_id)
    except RequestError, msg:
        raise YouTubeVideoError(str(msg))

    title = entry.media.title.text
    description = entry.media.description.text
    thumbnail_url = ''
    thumbnail_alternatives = []
    for thumbnail in entry.media.thumbnail:
        if (thumbnail.width, thumbnail.height) == ('120','90'):
            thumbnail_url = thumbnail.url
            thumbnail_alternatives.append(thumbnail_url)
    
    #PrintEntryDetails(entry)
    
    embed_src_template = Template("""
    <object width="$width" height="$height">
    <param name="movie" value="$media_url"></param>
     <param name="allowFullScreen" value="true"></param>
     <param name="allowscriptaccess" value="always"></param>
     <embed src="$media_url"
     type="application/x-shockwave-flash" allowscriptaccess="always" 
     allowfullscreen="true" width="$width" height="$height"></embed>
    </object>
    """)
    variables = dict(height=344, width=425,
                     media_url=entry.GetSwfUrl(),
                     )
                     
    embed_src = embed_src_template.substitute(variables).strip()

    return dict(title=title, embed_src=embed_src, description=description,
                thumbnail_url=thumbnail_url,
                thumbnail_alternatives=thumbnail_alternatives)
        
