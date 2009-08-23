from testbase import TestCase
from djangopeople.youtube import YouTubeVideoError, get_youtube_video_by_id

class YouTubeTestCase(TestCase):
    
    def test_video_by_youtube_video_id(self):
        # first test that you can get to the youtube video ID or (lazily)
        # by the youtube URL
        url = "http://www.youtube.com/watch?v=vcdgLclFWOU"
        
        func = get_youtube_video_by_id
        
        embed_src, description = func(url)
        
        
        
