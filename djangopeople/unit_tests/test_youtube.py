from testbase import TestCase
from djangopeople.youtube import YouTubeVideoError, get_youtube_video_by_id, \
  video_url_or_id


class YouTubeTestCase(TestCase):
    
    def test_video_url_or_id(self):
        """by entering a URL or an ID we get the ID"""
        func = video_url_or_id
        
        # super easy
        self.assertEqual(func("vcdgLclFWOU"), "vcdgLclFWOU")
        
        # easy
        self.assertEqual(func("http://www.youtube.com/watch?v=vcdgLclFWOU"),
                         "vcdgLclFWOU")
        
        # pretty easy
        
        self.assertEqual(func("http://www.youtube.com/v/vcdgLclFWOU&f=videos&app=youtube_gdata"),
                         "vcdgLclFWOU")
        
        # will fail (no v)
        self.assertRaises(YouTubeVideoError, func,
                          "http://www.google.com")
        
        self.assertRaises(YouTubeVideoError, func,
                          "http://www.youtube.com/watch?v=")
        
                              
        
    
    def test_video_by_youtube_video_id(self):
        # first test that you can get to the youtube video ID or (lazily)
        # by the youtube URL
        url = "http://www.youtube.com/watch?v=vcdgLclFWOU"
        
        func = get_youtube_video_by_id
        
        data = func(url)
        self.assertTrue(data.get('embed_src'))
        self.assertTrue('http://www.youtube.com/v/vcdgLclFWOU?f=videos&app=youtube_gdata' \
                        in data['embed_src'])
        self.assertTrue(data.get('title'))
        self.assertEqual(data['title'], 'Dengue Fever - One Thousand Tears Of A Tarantula')
        
        self.assertTrue(data.get('description'))
        self.assertEqual(data['description'], 'Dengue Fever')
        
        self.assertTrue(data.get('thumbnail_url'))
        
        
