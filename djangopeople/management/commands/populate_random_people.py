import os
import random

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction

from djangopeople.models import User, Country, KungfuPerson
from djangopeople.views import _get_or_create_style
from djangopeople.views import _get_or_create_club


class Command(BaseCommand):
    help = """populate random people"""
    
    random_people = list()
    random_places = list()
    random_styles = list()
    random_clubs = list()
    
    def handle(self, *args, **options):
        
        transaction.enter_transaction_management()
        transaction.managed(True)
        
        self._init_random_people()
        self._init_random_places()
        self._init_random_styles()
        self._init_random_clubs()
        
        number = 10
        if args:
            number = int(args[0])
            
            
        # do what the signup does
        for i in range(number):
            self._populate_random_person()
        
        transaction.commit()
        #transaction.rollback()

    def _init_random_styles(self):
        dir_ = os.path.dirname(__file__)
        for line in open(os.path.join(dir_, 'randomstyles.txt')):
            
            style = line.strip()
            if not style:
                continue
                
            self.random_styles.append((style,))
            
    def _init_random_clubs(self):
        dir_ = os.path.dirname(__file__)
        for line in open(os.path.join(dir_, 'randomclubs.txt')):
            try:
                name, url = \
                  [x.strip() for x in line.strip().split('|')]
            except ValueError:
                continue
            self.random_clubs.append((name, url))
            

    def _init_random_people(self):
        dir_ = os.path.dirname(__file__)
        for line in open(os.path.join(dir_, 'randompeople.txt')):
            try:
                username, first_name, last_name, email = \
                  [x.strip() for x in line.strip().split('|')]
            except ValueError:
                continue
            self.random_people.append((username, first_name, last_name, email))
            
    def _init_random_places(self):
        dir_ = os.path.dirname(__file__)
        for line in open(os.path.join(dir_, 'randomplaces.txt')):
            try:
                longitude, latitude, country_name, place_name, country_code = \
                  [x.strip() for x in line.strip().split('|')]
            except ValueError:
                continue
            self.random_places.append((longitude, latitude, country_name, place_name, country_code))
        
    def _populate_random_person(self):
        username, first_name, last_name, email = random.choice(self.random_people)
        print username, first_name, last_name, email
        longitude, latitude, country_name, place_name, country_code = random.choice(self.random_places)
        print longitude, latitude, country_name, place_name, country_code
        
        username += random.choice(list('qwertyuiopasdfghjklzxcvbnm')) +  'random'
        
        # now do the same as the sign up almost
        
        user = User.objects.create(username=username, email=email,
                                   password='test123')
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        region = None
        
        person = KungfuPerson.objects.create(
            user = user,
            country = Country.objects.get(
                iso_code = country_code
            ),
            region = region,
            latitude = latitude,
            longitude = longitude,
            location_description = place_name
        )
        
        if random.randint(1,4)!=1:
            (name,) = random.choice(self.random_styles)
            slug = name.strip().replace(' ', '-').lower()
            if name:
                style = _get_or_create_style(name)
                style.slug = slug
                style.save()
                person.styles.add(style)
                
                
        if random.randint(1,4) != 1:
            name, url = random.choice(self.random_clubs)
            slug = name.strip().replace(' ', '-').lower()
            if url or name:
                club = _get_or_create_club(url, name)
                club.slug = slug
                club.save()
                person.club_membership.add(club)
                person.save()
                
        
            
    
    
        