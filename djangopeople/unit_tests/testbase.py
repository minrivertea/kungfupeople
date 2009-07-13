# django
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User

# app
from djangopeople.models import KungfuPerson, Country

class TestCase(DjangoTestCase):
    def _create_person(self, username, email, password="secret", 
                       first_name="", last_name="",
                       country="United Kingdom",
                       region=None,
                       latitude=51.532601866,
                       longitude=-0.108382701874):
        
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
                                             newsletter='html')

        return user, person

    