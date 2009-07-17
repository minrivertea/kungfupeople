"""
testing views
"""
import os
from django.utils import simplejson
from django.conf import settings
from django.utils import simplejson

from djangopeople.models import KungfuPerson, Club, Country, Style, \
  DiaryEntry, Photo
from djangopeople import views
from testbase import TestCase

_original_MIDDLEWARE_CLASSES = settings.MIDDLEWARE_CLASSES

class ViewsTestCase(TestCase):
    
    def tearDown(self):
        # restore settings
        settings.MIDDLEWARE_CLASSES = _original_MIDDLEWARE_CLASSES
        # delete any upload thumbnails
        thumbnails_root = os.path.join(settings.MEDIA_ROOT,
                                       'photos', 
                                       'upload-thumbnails')
        if os.path.isdir(thumbnails_root):
            for f in os.listdir(thumbnails_root):
                f = os.path.join(thumbnails_root, f)
                if os.path.isdir(f):
                    for filename in os.listdir(f):
                        if os.path.isfile(os.path.join(f, filename)):
                            os.remove(os.path.join(f, filename))
                    if not os.listdir(f):
                        os.rmdir(f)
            if not os.listdir(thumbnails_root):
                os.rmdir(thumbnails_root)
        
        # delete any 
        for dir_ in [x.get_person_upload_folder() for x in KungfuPerson.objects.all()]:
            if os.path.isdir(dir_):
                for f in os.listdir(dir_):
                    if os.path.isfile(os.path.join(dir_, f)):
                        os.remove(os.path.join(dir_, f))
                if not os.listdir(dir_):
                    os.rmdir(dir_)
        
        super(ViewsTestCase, self).tearDown()
    
    
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
        
        
    
    def test_signup_basic(self):
        """test posting to signup"""
        # load from fixtures
        example_country = Country.objects.all().order_by('?')[0]
        
        response = self.client.post('/signup/', 
                                    dict(username='bob',
                                         email='bob@example.org',
                                         password1='secret',
                                         password2='secret',
                                         first_name=u"Bob",
                                         last_name=u"Sponge",
                                         region='',
                                         country=example_country.iso_code,
                                         latitude=1.0,
                                         longitude=-1.0,
                                         location_description=u"Hell, Pergatory",
                                        ))
        self.assertEqual(response.status_code, 302)
        
        self.assertEqual(KungfuPerson.objects.\
           filter(user__username="bob").count(), 1)


    def test_signup_multiple_styles(self):
        """test posting to signup and say that you have multiple styles
        by entering it with a comma"""
        # load from fixtures
        example_country = Country.objects.all().order_by('?')[0]
        
        response = self.client.post('/signup/', 
                                    dict(username='bob',
                                         email='bob@example.org',
                                         password1='secret',
                                         password2='secret',
                                         first_name=u"Bob",
                                         last_name=u"Sponge",
                                         region='',
                                         country=example_country.iso_code,
                                         latitude=1.0,
                                         longitude=-1.0,
                                         location_description=u"Hell, Pergatory",
                                         style=u"Fat style, Chocolate rain"
                                        ))
        self.assertEqual(response.status_code, 302)
        
        self.assertEqual(KungfuPerson.objects.\
           filter(user__username="bob").count(), 1)
        
        # This should now have created 2 styles
        self.assertEqual(Style.objects.all().count(), 2)
        self.assertEqual(Style.objects.filter(name="Fat style").count(), 1)
        self.assertEqual(Style.objects.filter(name="Chocolate rain").count(), 1)
        

        
    def test_newsletter_options(self):
        """test changing your newsletter options"""
        
        user, person = self._create_person('bob', 'bob@example.com',
                                           )
        
        default = person.newsletter
        
        # change it to plain
        response = self.client.post('/bob/newsletter/options/',
                                    dict(newsletter='plain'))
        self.assertEqual(response.status_code, 403) # forbidden
        
        #self.client.login(username="bob", password="secret")
        self.client.post('/login/', dict(username="bob", password="secret"))
        
        r=self.client.get('/')
        response = self.client.post('/bob/newsletter/options/',
                                    dict(newsletter='plain'))
        
        # THIS DOES NOT WORK!!!
        # WHY IS THE LOGIN NOT TAKING EFFECT?????
        self.assertEqual(response.status_code, 302) # redirect
        
    def test_diary_entry_location_json(self):
        """test getting the json for a diary entry"""
        
        country = Country.objects.all().order_by('?')[0]

        user, person = self._create_person('bob', 'bob@example.com',
                                           password="secret")
        # that person has to have a diary entry
        entry = DiaryEntry.objects.create(user=user, title=u"Title",
                                          slug="title",
                                          content=u"Content",
                                          is_public=True,
                                          country=country,
                                          latitude=2.2,
                                          longitude=-1.1,
                                          location_description=u"Hell")
        
        response = self.client.get(entry.get_absolute_url()+'location.json')
        self.assertEqual(response.status_code, 403) # because you're not logged in
        
        # but if you log in it should be ok
        self.client.login(username="bob", password="secret")
        
        response = self.client.get(entry.get_absolute_url()+'location.json')
        self.assertEqual(response.status_code, 200)
        
        data = simplejson.loads(response.content)
        self.assertEqual(data['latitude'], 2.2)
        self.assertEqual(data['longitude'], -1.1)
        self.assertEqual(data['country'], country.iso_code)
        self.assertEqual(data['location_description'], u"Hell")
        
    def test_photo_upload_multiple_basic(self):
        """add a couple of photos first into the upload folder then
        run /username/photo/upload/ with some description and some
        location.
        """
        
        # disable the
        mdc = list(settings.MIDDLEWARE_CLASSES)
        try:
            mdc.remove('django.contrib.csrf.middleware.CsrfMiddleware')
            settings.MIDDLEWARE_CLASSES = tuple(mdc)
        except ValueError:
            # not there
            pass
        
        country = Country.objects.all().order_by('?')[0]

        user, person = self._create_person('bob', 'bob@example.com',
                                           password="secret")
        
        # by default the photo/upload/ page will expect you to use
        # the swfupload
        self.client.login(username="bob", password="secret")
        
        upload_url = person.get_absolute_url() + 'photo/upload/'
        response = self.client.get(upload_url)
        assert response.status_code == 200
        self.assertFalse(response.content.count('type="file"'))
        
        # now upload some photos to the pre/ method
        pre_upload_url = upload_url + 'pre/'
        photo1 = open(os.path.join(os.path.dirname(__file__), 'P1000898.jpg'))
        photo2 = open(os.path.join(os.path.dirname(__file__), 'P1010051.jpg'))
        from django.core.files import File
        file1 = File(photo1)
        file2 = File(photo2)
        
        response = self.client.post(pre_upload_url, dict(Filename='P1000898.jpg',
                                                         Filedata=file1))
        self.assertEqual(response.status_code, 200)
        # response.content is now a url to a thumbnail
        thumbnail_url = response.content
        self.assertTrue(thumbnail_url.endswith('.jpg'))
        
        # the actual file is located in...
        file_path = os.path.join(settings.MEDIA_ROOT, 
                                thumbnail_url.replace('/static/',''))
        # you can view this
        image_response = self.client.get(thumbnail_url)
        
        assert image_response.status_code == 200
        import stat
        self.assertEqual(len(image_response.content), 
                         os.stat(file_path)[stat.ST_SIZE])
        
        # upload another one
        response = self.client.post(pre_upload_url, dict(Filename='P1010051.jpg',
                                                         Filedata=file2))
        
        # there should now be two temporary photos uploaded
        self.assertEqual(len(os.listdir(person.get_person_upload_folder())), 2)
        
        self.assertEqual(Photo.objects.filter(user=user).count(), 0)
        # Now, continue with submitting the photo upload form
        photo_upload_url = person.get_absolute_url() + 'photo/upload/'
        response = self.client.post(photo_upload_url, 
                                    dict(country=country.iso_code,
                                         location_description=u"Hell",
                                         latitude=1.0,
                                         longitude=-2.0,
                                         description=u"Some description"
                                        ))
        self.assertEqual(response.status_code, 302)
        redirected_to = response._headers['location'][1]
        self.assertTrue(redirected_to.endswith('/done/'))
        
        self.assertEqual(Photo.objects.filter(user=user).count(), 2)
        for photo in Photo.objects.filter(user=user):
            self.assertEqual(photo.location_description, u"Hell")
            self.assertEqual(photo.country, country)
            self.assertEqual(photo.latitude, 1.0)
            self.assertEqual(photo.longitude, -2.0)
            
        
    def test_photo_upload_single_basic(self):
        """same as test_photo_upload_multiple_basic
        but this time prefer with single.
        """
        
        # disable the
        mdc = list(settings.MIDDLEWARE_CLASSES)
        try:
            mdc.remove('django.contrib.csrf.middleware.CsrfMiddleware')
            settings.MIDDLEWARE_CLASSES = tuple(mdc)
        except ValueError:
            # not there
            pass
        
        country = Country.objects.all().order_by('?')[0]

        user, person = self._create_person('bob', 'bob@example.com',
                                           password="secret")
        
        # by default the photo/upload/ page will expect you to use
        # the swfupload
        self.client.login(username="bob", password="secret")
        
        upload_url = person.get_absolute_url() + 'photo/upload/'
        response = self.client.get(upload_url, dict(prefer='single'))
        assert response.status_code == 200
        self.assertTrue(response.content.count('type="file"'))

        photo1 = open(os.path.join(os.path.dirname(__file__), 'P1000898.jpg'))
        photo2 = open(os.path.join(os.path.dirname(__file__), 'P1010051.jpg'))
        from django.core.files import File
        file1 = File(photo1)
        
        self.assertEqual(Photo.objects.filter(user=user).count(), 0)
        # Now, continue with submitting the photo upload form
        photo_upload_url = person.get_absolute_url() + 'photo/upload/'
        response = self.client.post(photo_upload_url, 
                                    dict(country=country.iso_code,
                                         location_description=u"Hell",
                                         latitude=1.0,
                                         longitude=-2.0,
                                         description=u"Some description",
                                         photo=file1,
                                        ))
        self.assertEqual(response.status_code, 302)
        redirected_to = response._headers['location'][1]
        self.assertTrue(redirected_to.endswith('/done/'))
        

        
        
                        


