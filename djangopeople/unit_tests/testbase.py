# django
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.conf import settings

# app
from djangopeople.models import KungfuPerson, Country, Club, Style, DiaryEntry
from djangopeople.utils import unaccent_string

_original_PROWL_API_KEY = settings.PROWL_API_KEY

class TestCase(DjangoTestCase):
    
    
    def setUp(self):
        settings.PROWL_API_KEY = None
        super(TestCase, self).setUp()
        
    def tearDown(self):
        # restore settings
        settings.PROWL_API_KEY = _original_PROWL_API_KEY
        super(TestCase, self).tearDown()
        
    
    # This is repeated in ../newsletter/unit_tests so I need to refactor that 
    # one day
    def _create_person(self, username, email, password="secret", 
                       first_name="", last_name="",
                       country="United Kingdom",
                       region=None,
                       latitude=51.532601866,
                       longitude=-0.108382701874,
                       location_description=u"Hell"):
        
        user = User.objects.create_user(username=username,
                                        email=email,
                                        password=password)
        if first_name or last_name:
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
        country = Country.objects.get(name=country)
        person = KungfuPerson.objects.create(user=user,
                                             country=country,
                                             region=region,
                                             latitude=latitude,
                                             longitude=longitude,
                                             location_description=location_description,
                                             newsletter='html')

        return user, person
    
    def _create_club(self, name, slug=None, url="", description=""):
        if slug is None:
            slug = slugify(unaccent_string(name))
        try:
            club = Club.objects.get(slug=slug)
        except Club.DoesNotExist:
            club = Club.objects.create(name=name, slug=slug)
        club.url = url
        club.description = description
        club.save()
        return club

    def _create_style(self, name, slug=None, url="", description=""):
        if slug is None:
            slug = slugify(unaccent_string(name))
        try:
            style = Style.objects.get(slug=slug)
        except Style.DoesNotExist:
            style = Style.objects.create(name=name, slug=slug)
        style.url = url
        style.description = description
        style.save()
        return style

    def _create_diary_entry(self, user, title, content, slug=None, is_public=True,
                            country="United Kingdom",
                            region=None,
                            latitude=51.532601866,
                            longitude=-0.108382701874,
                            location_description=u"Hell"):
        if slug is None:
            slug = slugify(unaccent_string(title))
        try:
            diary_entry = DiaryEntry.objects.get(slug=slug, user=user)
        except DiaryEntry.DoesNotExist:
            country = Country.objects.get(name=country)
            diary_entry = DiaryEntry.objects.create(user=user, title=title, 
                                                    content=content, slug=slug,
                                                    country=country,
                                                    region=region,
                                                    latitude=latitude,
                                                    longitude=longitude,
                                                    location_description=location_description)
        diary_entry.is_public = bool(is_public)
        diary_entry.save()
        return diary_entry

    