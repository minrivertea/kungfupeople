# django
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

# app
from djangopeople.models import KungfuPerson, Country, Club
from djangopeople.utils import unaccent_string

class TestCase(DjangoTestCase):
    
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

    