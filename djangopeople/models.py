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
        raise NotImplementedError, "This doesn't work in postgres"
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
        ## mysql
        #cursor.execute("""
        #    SELECT
        #        djangopeople_region.id, count(*) AS peoplecount
        #    FROM
        #        djangopeople_kungfuperson, djangopeople_region
        #    WHERE
        #        djangopeople_region.id = djangopeople_kungfuperson.region_id
        #    AND
        #        djangopeople_region.country_id = %d
        #    GROUP BY djangopeople_kungfuperson.region_id
        #    ORDER BY peoplecount DESC
        #""" % self.id)
        
        ## postgresql
        cursor.execute("""
            SELECT
                djangopeople_region.id, count(*) AS peoplecount
            FROM
                djangopeople_region
            WHERE
            --    djangopeople_region.id = djangopeople_kungfuperson.region_id
            -- AND
                djangopeople_region.country_id = %d
            GROUP BY djangopeople_region.id
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
    logo = models.ImageField(blank=True, upload_to='clubs')
    add_date = models.DateField('date added', default=datetime.now)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Clubs"
        
    def get_absolute_url(self):
        if self.slug:
            return "/club/%s/" % self.slug
        else:
            return "/club/%s/" % self.id


class Style(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField()
    description = models.TextField()
    add_date = models.DateField('date added', default=datetime.now)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Styles"
        
    def get_absolute_url(self):
        return "/style/%s/" % self.slug

class DiaryEntry(models.Model):
    class Meta:
        verbose_name_plural = "Diary entries"
        
    user = models.ForeignKey(User)
    
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    content = models.TextField()
    date_added = models.DateTimeField('date added', default=datetime.now)
    #tags = 
    is_public = models.BooleanField(default=False)

    # Location stuff - all location fields are required
    country = models.ForeignKey(Country)
    region = models.ForeignKey(Region, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_description = models.CharField(max_length=50)

    def __unicode__(self):
        return self.title

        
    def get_absolute_url(self):
        return '/%s/diary/%s/' % (self.user.username, self.slug)

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
        
    def get_photos(self):
        return Photo.objects.filter(diary_entry=self).order_by('-date_added')


class Photo(models.Model):
    user = models.ForeignKey(User)
    diary_entry = models.ForeignKey(DiaryEntry, blank=True, null=True)
    slug = models.SlugField()
    description = models.TextField()
    photo = models.ImageField(blank=True, upload_to='photos')
    date_added = models.DateTimeField('date added', default=datetime.now)

    # Location stuff - all location fields are required
    country = models.ForeignKey(Country)
    region = models.ForeignKey(Region, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_description = models.CharField(max_length=50)


    def __unicode__(self):
        return self.photo
    
    def __repr__(self):
        return '<%s: %s %r>' % (self.__class__.__name__, self.photo.name, self.slug)

    class Meta:
        verbose_name_plural = "Photos"

    def get_absolute_url(self):
        return "/%s/photo/%s/" % (self.user.username, self.id)
        
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
    
from django.db import connection
from string import Template
    
class DistanceManager(models.Manager):

    
    def nearest_to(self, point, number=20, within_range=None, offset=0,
                   extra_where_sql=''):
        """finds the model objects nearest to a given point
        
        `point` is a tuple of (x, y) in the spatial ref sys given by `from_srid`
        
        returns a list of tuples, sorted by increasing distance from the given `point`. 
        each tuple being (model_object, dist), where distance is in the units of the 
        spatial ref sys given by `to_srid`"""
        if not isinstance(point, tuple):
            raise TypeError
        
        cursor = connection.cursor()
        x, y = point
        table = self.model._meta.db_table
        distance_clause = ''
        if within_range:
            # Need to turn the select below into a subquery so I can do where distance <= X
            raise NotImplementedError, "Not supported yet"
        
        if extra_where_sql or distance_clause:
            extra_where_sql = 'WHERE\n\t' + extra_where_sql
        sql = Template("""
            SELECT 
              gl.id,
              ATAN2(
                SQRT(
                  POW(COS(RADIANS($x)) *
                      SIN(RADIANS(gl.latitude - $y)), 2) + 
                  POW(COS(RADIANS(gl.longitude)) * SIN(RADIANS($x)) - 
                      SIN(RADIANS(gl.longitude)) * COS(RADIANS($x)) * 
                      COS(RADIANS(gl.latitude - $y)), 2)), 
                 (SIN(RADIANS(gl.longitude)) * SIN(RADIANS($x)) + 
                  COS(RADIANS(gl.longitude)) * COS(RADIANS($x)) * 
                  COS(RADIANS(gl.latitude - $y)))
                ) * 6372.795 AS distance
            FROM 
              djangopeople_kungfuperson gl
            
              %s
              %s
            ORDER BY distance ASC
            LIMIT $number
            OFFSET $offset
            ;
        """ % (extra_where_sql, distance_clause))
        sql_string = sql.substitute(locals())
        cursor.execute(sql_string)
        nearbys = cursor.fetchall()
        # get a list of primary keys of the nearby model objects
        ids = [p[0] for p in nearbys]
        # get a list of distances from the model objects
        dists = [p[1] for p in nearbys]
        #print [p for p in nearbys]
        places = self.filter(id__in=ids)
        # the QuerySet comes back in an undefined order; let's
        # order it by distance from the given point
        def order_by(objects, listing, name):
            """a convenience method that takes a list of objects,
            and orders them by comparing an attribute given by `name`
            to a sorted listing of values of the same length."""
            sorted = []
            for i in listing:
                for obj in objects:
                    if getattr(obj, name) == i:
                        sorted.append(obj)
            return sorted
        return zip(order_by(places, ids, 'id'), dists)

    
    
class KungfuPerson(models.Model):
    user = models.ForeignKey(User, unique=True)
    bio = models.TextField(blank=True)
    styles = models.ManyToManyField(Style)
    club_membership = models.ManyToManyField(Club)
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
    
    
    objects = DistanceManager()

    class Meta:
        verbose_name_plural = 'Kung fu people'

    class Admin:
        list_display = ('user', 'profile_views')


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
            
    def get_clubs(self):
        return self.club_membership.all()
    
    def get_styles(self):
        return self.styles.all()
    

class CountrySite(models.Model):
    "Community sites for various countries"
    title = models.CharField(max_length = 100)
    url = models.URLField(max_length = 255)
    country = models.ForeignKey(Country)
    
    def __unicode__(self):
        return '%s <%s>' % (self.title, self.url)
   
    class Admin:
        pass
