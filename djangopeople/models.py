from datetime import datetime
from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.contenttypes import generic
from lib.geopy import distance
from django.utils.safestring import mark_safe
from django.utils.html import escape

RESERVED_USERNAMES = set((
    # Trailing spaces are essential in these strings, or split() will be buggy
    'feed www help security porn manage smtp fuck pop manager api owner shit '
    'secure ftp discussion blog features test mail email administrator '
    'xmlrpc web xxx pop3 abuse atom complaints news information imap cunt rss '
    'info pr0n about forum admin weblog team feeds root about info news blog '
    'forum features discussion email abuse complaints map skills tags ajax '
    'comet poll polling thereyet filter search zoom machinetags search django '
    'people profiles profile person navigate nav browse manage static css img '
    'javascript js code flags flag country countries region place places '
    'photos owner maps upload geocode geocoding login logout openid openids '
    'recover lost signup reports report flickr upcoming mashups recent irc '
    'group groups bulletin bulletins messages message newsfeed events company '
    'companies active'
).split())

class CountryManager(models.Manager):
    def top_countries(self):
        # Returns populated countries in order of population
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                djangopeople_country.id, count(*) AS peoplecount
            FROM
                djangopeople_kungfuperson, djangopeople_country
            WHERE
                djangopeople_country.id = djangopeople_kungfuperson.country_id
            GROUP BY country_id
            ORDER BY peoplecount DESC
        """)
        rows = cursor.fetchall()
        found = self.in_bulk([r[0] for r in rows])
        countries = []
        for row in rows:
            country = found[row[0]]
            country.peoplecount = row[1]
            countries.append(country)
        return countries

class Country(models.Model):
    # Longest len('South Georgia and the South Sandwich Islands') = 44
    name = models.CharField(max_length=50)
    iso_code = models.CharField(max_length=2, unique=True)
    iso_numeric = models.CharField(max_length=3, unique=True)
    iso_alpha3 = models.CharField(max_length=3, unique=True)
    fips_code = models.CharField(max_length=2, unique=True)
    continent = models.CharField(max_length=2)
    # Longest len('Grand Turk (Cockburn Town)') = 26
    capital = models.CharField(max_length=30, blank=True)
    area_in_sq_km = models.FloatField()
    population = models.IntegerField()
    currency_code = models.CharField(max_length=3)
    # len('en-IN,hi,bn,te,mr,ta,ur,gu,ml,kn,or,pa,as,ks,sd,sa,ur-IN') = 56
    languages = models.CharField(max_length=60)
    geoname_id = models.IntegerField()

    # Bounding boxes
    bbox_west = models.FloatField()
    bbox_north = models.FloatField()
    bbox_east = models.FloatField()
    bbox_south = models.FloatField()
    
    # De-normalised
    num_people = models.IntegerField(default=0)
    
    objects = CountryManager()
    
    def top_regions(self):
        # Returns populated regions in order of population
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("""
            SELECT
                djangopeople_region.id, count(*) AS peoplecount
            FROM
                djangopeople_kungfuperson, djangopeople_region
            WHERE
                djangopeople_region.id = djangopeople_kungfuperson.region_id
            AND
                djangopeople_region.country_id = %d
            GROUP BY djangopeople_kungfuperson.region_id
            ORDER BY peoplecount DESC
        """ % self.id)
        rows = cursor.fetchall()
        found = Region.objects.in_bulk([r[0] for r in rows])
        regions = []
        for row in rows:
            region = found[row[0]]
            region.peoplecount = row[1]
            regions.append(region)
        return regions
    
    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Countries'
    
    def __unicode__(self):
        return self.name
    
    class Admin:
        pass

class Region(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=50)
    country = models.ForeignKey(Country)
    flag = models.CharField(max_length=100, blank=True)
    
#    geoname_id = models.IntegerField()
    bbox_west = models.FloatField()
    bbox_north = models.FloatField()
    bbox_east = models.FloatField()
    bbox_south = models.FloatField()
    
    # De-normalised
    num_people = models.IntegerField(default=0)
    
    def get_absolute_url(self):
        return '/%s/%s/' % (self.country.iso_code.lower(), self.code.lower())
    
    def __unicode__(self):
        return self.name
    
    class Meta:
        ordering = ('name',)
    
    class Admin:
        pass

class Club(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField()
    url = models.URLField()
    description = models.TextField()
    logo = models.ImageField(blank=True, upload_to='logos')
    add_date = models.DateField('date added', default=datetime.now)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Clubs"

    
class Video(models.Model):
    user = models.ForeignKey(User)
    embed_src = models.TextField()
    description = models.TextField(blank=True)
    add_date = models.DateField('date added', default=datetime.now)
    approved = models.BooleanField(default=True)
    
    class Meta:
        ordering = ('-add_date',)
        
    def __unicode__(self):
        return self.description and self.description.replace('\n', ' ')\
          or self.embed_src[:40]
    
class KungfuPerson(models.Model):
    user = models.ForeignKey(User, unique=True)
    bio = models.TextField(blank=True)
    style = models.CharField(max_length=200)
    personal_url = models.URLField()
    club_membership = models.ManyToManyField(Club)
    trivia = models.TextField(blank=True)
    privacy_email = models.BooleanField()
    what_is_kungfu = models.CharField(max_length=144, blank=False)
    
    # Location stuff - all location fields are required
    country = models.ForeignKey(Country)
    region = models.ForeignKey(Region, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_description = models.CharField(max_length=50)
    
    # Profile photo
    photo = models.ImageField(blank=True, upload_to='profiles')
    
    # Stats
    profile_views = models.IntegerField(default=0)
     
    def get_nearest(self, num=5):
        "Returns the nearest X people, but only within the same continent"
        # TODO: Add caching
        
        people = list(self.country.kungfuperson_set.select_related().exclude(pk=self.id))
        if len(people) <= num:
            # Not enough in country; use people from the same continent instead
            people = list(KungfuPerson.objects.filter(
                country__continent = self.country.continent,
            ).exclude(pk=self.id).select_related())

        # Sort and annotate people by distance
        for person in people:
            person.distance_in_miles = distance.VincentyDistance(
                (self.latitude, self.longitude),
                (person.latitude, person.longitude)
            ).miles
        
        # Return the nearest X
        people.sort(key=lambda x: x.distance_in_miles)
        return people[:num]
    
    def location_description_html(self):
        region = ''
        if self.region:
            region = '<a href="%s">%s</a>' % (
                self.region.get_absolute_url(), self.region.name
            )
            bits = self.location_description.split(', ')        
            if len(bits) > 1 and bits[-1] == self.region.name:
                bits[-1] = region
            else:
                bits.append(region)
                bits[:-1] = map(escape, bits[:-1])
            return mark_safe(', '.join(bits))
        else:
            return self.location_description
    
    def __unicode__(self):
        return unicode(self.user.get_full_name())
    
    def get_absolute_url(self):
        return '/%s/' % self.user.username
    
    def save(self, force_insert=False, force_update=False): # TODO: Put in transaction
        # Update country and region counters
        super(KungfuPerson, self).save(force_insert=force_insert, force_update=force_update)
        self.country.num_people = self.country.kungfuperson_set.count()
        self.country.save()
        if self.region:
            self.region.num_people = self.region.kungfuperson_set.count()
            self.region.save()
    
    class Meta:
        verbose_name_plural = 'Kung fu people'

    class Admin:
        list_display = ('user', 'profile_views')


class CountrySite(models.Model):
    "Community sites for various countries"
    title = models.CharField(max_length = 100)
    url = models.URLField(max_length = 255)
    country = models.ForeignKey(Country)
    
    def __unicode__(self):
        return '%s <%s>' % (self.title, self.url)
   
    class Admin:
        pass
