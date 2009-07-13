"""
testing views
"""
import os
from django.utils import simplejson

from django.test import TestCase
from djangopeople.models import KungfuPerson, Club

from djangopeople import views

class ViewsTestCase(TestCase):
    def test_guess_club_name(self):
        """Test signup"""
        
        response = self.client.get('/guess-club-name.json?club_url=')
        assert response.status_code==200
        result = simplejson.loads(response.content)
        self.assertTrue('error' in result)
        self.assertTrue('club_name' not in result)
        
        # add a club
        Club.objects.create(name=u"Fujian White Crane",
                            url=u"http://www.fwckungfu.com")
        
        # spelling it without http
        response = self.client.get('/guess-club-name.json?club_url=www.fwckungfu.com')
        assert response.status_code==200
        result = simplejson.loads(response.content)
        self.assertTrue('error' not in result)
        self.assertTrue('club_name' in result)
        
        # spelling it without http
        response = self.client.get('/guess-club-name.json?club_url=www.fwckungfu.com')
        assert response.status_code==200
        result = simplejson.loads(response.content)
        self.assertTrue('error' not in result)
        self.assertEqual(result['club_name'], u"Fujian White Crane")
        
        # spelling it with http:// and /index.html
        response = self.client.get('/guess-club-name.json?club_url=http://www.fwckungfu.com/index.html')
        assert response.status_code==200
        result = simplejson.loads(response.content)
        self.assertTrue('error' not in result)
        self.assertEqual(result['club_name'], u"Fujian White Crane")
        
    def test_guess_club_name_remotely(self):
        """test guessing a club name by downloading the <title> for the URL"""
        
        def run(url):
            response = self.client.get('/guess-club-name.json?club_url=%s' % url)
            assert response.status_code==200
            return simplejson.loads(response.content)

        examples_dir = os.path.join(os.path.dirname(__file__), 'example_kung_sites')
        def get_url(filename):
            return "file://" + os.path.join(examples_dir, filename)
        
        result = run(get_url("fwc.html"))
        self.assertTrue('error' not in result)
        self.assertTrue('club_name' in result)
        self.assertEqual(result['club_name'], u"Fujian White Crane Kung Fu Club")
        
        result = run(get_url("kamonwingchun.html"))
        self.assertTrue('error' not in result)
        self.assertTrue('club_name' in result)
        self.assertEqual(result['club_name'], u"Kamon Martial Art Federation")
        
        result = run(get_url("kungfulondon.html"))
        self.assertTrue('error' not in result)
        self.assertTrue('club_name' in result)
        self.assertEqual(result['club_name'], u"Hung Leng Kuen Kung Fu, London")
                
        result = run(get_url("shaolintemplateuk.html"))
        self.assertTrue('error' not in result)
        self.assertTrue('club_name' in result)
        self.assertEqual(result['club_name'], u"Shaolin Temple UK")
        
        result = run(get_url("wengchun.html"))
        self.assertTrue('error' not in result)
        self.assertTrue('club_name' in result)
        self.assertEqual(result['club_name'], u"London Shaolin Weng Chun Kung Fu Academy")
        
        result = run(get_url("wingchun-escrima.html"))
        self.assertTrue('error' not in result)
        self.assertTrue('club_name' in result)
        self.assertEqual(result['club_name'], u"Tao Wing Chun & Escrima Academy  London & Surrey")
        
        #result = run(get_url(""))
        #self.assertTrue('error' not in result)
        #self.assertTrue('club_name' in result)
        #self.assertEqual(result['club_name'], u"")
        
        result = run(get_url("namyang.html"))
        self.assertTrue('error' not in result)
        self.assertTrue('club_name' in result)
        self.assertEqual(result['club_name'], u"Shaolin Martial Arts: Nam Yang Kung Fu")
        
        
    
    #def test_signup(self):
    #    """test posting to signup"""
    #    
    #    assert False, "Work harder!"
        
        
        
        
