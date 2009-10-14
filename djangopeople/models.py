# python
import os
import uuid
from datetime import datetime
from string import Template
import logging

# django
from django.db import connection
from django.contrib import admin
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
from django.contrib.contenttypes import generic
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.db.models.signals import post_save, pre_save
from lib.geopy import distance
from django.contrib.sites.models import Site

from utils import prowlpy_wrapper as prowl


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
    'companies active clubs styles style club'
).split())


class DistanceManager(models.Manager):

    
    def nearest_to(self, point, number=20, within_range=None, offset=0,
                   extra_where_sql=''):
        """finds the model objects nearest to a given point
        
        `point` is a tuple of (x, y) in the spatial ref sys given by `from_srid`
        
        NB: (x,y) <=> (lat, long)
        
        returns a list of tuples, sorted by increasing distance from the given `point`. 
        each tuple being (model_object, dist), where distance is in the units of the 
        spatial ref sys given by `to_srid`"""
        if not isinstance(point, tuple):
            raise TypeError
        
        # this manager hack only works in mysql or postgres since sqlite3 doesn't
        # support the sqrt function.
        if settings.DATABASE_ENGINE == 'sqlite3':
            # but since running sqlite is so useful for running tests
            # we use a hack
            return self._manual_nearest_to(point, number=number, 
                                           within_range=within_range,
                                           offset=offset,
                                           extra_where_sql=extra_where_sql)
        
        cursor = connection.cursor()
        x, y = point # x=latitude, y=longitude
        table = self.model._meta.db_table
        
        
        if settings.DATABASE_ENGINE == 'mysql':
            if extra_where_sql:
                extra_where_sql = 'WHERE\n\t' + extra_where_sql
                
            template = Template("""
                SELECT 
                gl.id,
                ATAN2(
                    SQRT(
                    POW(COS(RADIANS($y)) *
                        SIN(RADIANS(gl.latitude - $x)), 2) +
                    POW(COS(RADIANS(gl.longitude)) * SIN(RADIANS($y)) -
                        SIN(RADIANS(gl.longitude)) * COS(RADIANS($y)) * 
                        COS(RADIANS(gl.latitude - $x)), 2)), 
                    (SIN(RADIANS(gl.longitude)) * SIN(RADIANS($y)) + 
                    COS(RADIANS(gl.longitude)) * COS(RADIANS($y)) * 
                    COS(RADIANS(gl.latitude - $x)))
                    ) * 6372.795 AS distance
                FROM 
                $table gl
                
                %s
                ORDER BY distance ASC
                LIMIT $number
                OFFSET $offset
                ;
            """ % (extra_where_sql,))
            sql_string = template.substitute(locals())
            
        else:
            # Postgres!
    
            distance_clause = ''
            if within_range:
                # do something
                distance_clause = Template("""
                miles_between_lat_long($x,$y, 
                                    gl.latitude::numeric, gl.longitude::numeric
                                    ) < %s
                """ % within_range
                                        ).substitute(locals())
                
            if extra_where_sql and distance_clause:
                distance_clause = 'AND\n\t' + distance_clause
            
            if extra_where_sql or distance_clause:
                extra_where_sql = 'WHERE\n\t' + extra_where_sql
                
                
            template = Template("""
                SELECT 
                gl.id,
                miles_between_lat_long($x, $y,
                                    gl.latitude::numeric, gl.longitude::numeric
                                    ) AS distance
    
                FROM 
                $table gl
                %s
                %s
                ORDER BY distance ASC
                LIMIT $number
                OFFSET $offset
                ;
            """ % (extra_where_sql, distance_clause))
            sql_string = template.substitute(locals())
            
        cursor.execute(sql_string)
        nearbys = cursor.fetchall()
        
        # get a list of primary keys of the nearby model objects
        ids = [p[0] for p in nearbys]
        # get a list of distances from the model objects
        dists = [p[1] for p in nearbys]
        places = self.filter(id__in=ids).select_related()
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
    
    
    def _manual_nearest_to(self, point, number=20, within_range=None, offset=0,
                           extra_where_sql=''):
        cursor = connection.cursor()
        # point -> (long, lat)
        #x, y = point
        table = self.model._meta.db_table
        if extra_where_sql and not extra_where_sql.strip().lower().startswith('where'):
            extra_where_sql = "WHERE %s" % extra_where_sql
        template = Template("""
            SELECT 
            gl.id,
            gl.latitude,
            gl.longitude
            FROM 
            $table gl
            
            %s
            ;
        """ % (extra_where_sql,))
        sql_string = template.substitute(locals())
        cursor.execute(sql_string)
        from math import sqrt 
        from geopy import distance as geopy_distance
        def distance(latitude, longitude):
            return geopy_distance.distance((point[0], point[1]), (latitude, longitude)).miles

        nearbys = []
        
        for id, latitude, longitude in cursor.fetchall():
            d = distance(latitude, longitude)
            if within_range:
                if d <= within_range:
                    nearbys.append([d, id])
            else:
                nearbys.append([d, id])
        nearbys.sort()
        nearbys = nearbys[:number]
        return [[self.get(id=y), x] for (x,y) in nearbys]
    
    def in_box(self, box):
        """ box is (left, upper, right, lower) """
        return self.filter(latitude__lt=box[0],
                           latitude__gt=box[2],
                           longitude__gt=box[1],
                           longitude__lt=box[3])
    


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
    
    @models.permalink
    def get_absolute_url(self):
        return ("country", (self.iso_code.lower(),))

class Region(models.Model):
    class Meta:
        ordering = ('name',)
        
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
    
    

class Club(models.Model):
    class Meta:
        verbose_name_plural = "Clubs"
        ordering = ('-date_added',)
        
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField()
    url = models.URLField()
    description = models.TextField(blank=True)
    logo = models.ImageField(blank=True, upload_to='clubs')
    date_added = models.DateTimeField('date added', default=datetime.now)
    clicks = models.IntegerField(default=0)
    
    def __unicode__(self):
        return self.name

    def get_members(self):
        members = KungfuPerson.objects.filter(club_membership=self)
        return members
        
    @models.permalink
    def get_absolute_url(self):
        if not self.slug:
            # TODO: This is slow and shouldn't happen but will happen
            # in the alpha phase till we sort out the club add stuff.
            from django.template.defaultfilters import slugify
            from utils import unaccent_string
            self.slug = slugify(unaccent_string(self.name))
            self.save()
            
        return ("club.view", (self.slug,))
    
def _club_saved(sender, instance, created, **__):
    cache_key = 'clubs_recent_5'
    cache.delete(cache_key)
    
post_save.connect(_club_saved, sender=Club,
                  dispatch_uid="_club_saved")

class Style(models.Model):
    class Meta:
        verbose_name_plural = "Styles"
        ordering = ('-date_added',)
        
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField()
    description = models.TextField()
    date_added = models.DateTimeField('date added', default=datetime.now)
    clicks = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

    @models.permalink 
    def get_absolute_url(self):
        if not self.slug:
            # TODO: This is slow and shouldn't happen but will happen
            # in the alpha phase till we sort out the club add stuff.
            from django.template.defaultfilters import slugify
            from utils import unaccent_string
            self.slug = slugify(unaccent_string(self.name[:50]))
            self.save()
        return ("style.view", (self.slug,))
    
def _style_saved(sender, instance, created, **__):
    cache_key = 'styles_recent_5'
    cache.delete(cache_key)
post_save.connect(_style_saved, sender=Style,
                  dispatch_uid="_style_saved")
    

class DiaryEntry(models.Model):
    class Meta:
        verbose_name_plural = "Diary entries"
        ordering = ('-date_added',)
        
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
    
    objects = DistanceManager()
    

    def __unicode__(self):
        return self.title

    def get_content(self):
        return self.content

    class Meta:
        verbose_name = "DiaryEntry"

    @models.permalink
    def get_absolute_url(self):
        return ("diaryentry.view", (self.user.username, self.slug))
        
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


def prowl_new_diary_entry(sender, instance, created, **__):
    description = "%s %s" % (instance.user.first_name, instance.user.last_name)
    site = Site.objects.get_current()
    description += "\nhttp://%s%s" % (site.domain, instance.get_absolute_url())
    if created and instance.is_public:
        try:
            prowl("Diary entry added",
                  description=description)
        except:
            logging.error("Unabled to prowl about new diary entry",
                          exc_info=True)
        
post_save.connect(prowl_new_diary_entry, sender=DiaryEntry,
                 dispatch_uid="prowl_new_diary_entry")


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

    objects = DistanceManager()

    class Meta:
        verbose_name_plural = "Photos"
        ordering = ('-date_added',)

    def __unicode__(self):
        return self.description

    def get_content(self):
        return self.photo

    class Meta:
        verbose_name = "Photo"
    
    def __repr__(self):
        return '<%s: %s %r>' % (self.__class__.__name__, self.photo.name, self.slug)

    @models.permalink
    def get_absolute_url(self):
        return ("photo.view", (self.user.username, self.id))
        
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

def prowl_new_photo(sender, instance, created, **__):
    description = "%s %s" % (instance.user.first_name, instance.user.last_name)
    site = Site.objects.get_current()
    description += "\nhttp://%s%s" % (site.domain, instance.get_absolute_url())
    if created:
        try:
            prowl("Photo added",
                  description=description)
        except:
            logging.error("Unabled to prowl about new photo",
                          exc_info=True)
            
        
post_save.connect(prowl_new_photo, sender=Photo)

    
class Video(models.Model):   
    user = models.ForeignKey(User)
    embed_src = models.TextField()
    title = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    youtube_video_id = models.CharField(max_length=100, blank=True, null=True)
    thumbnail_url = models.CharField(max_length=250, blank=True, null=True)
    date_added = models.DateTimeField('date added', default=datetime.now)
    approved = models.BooleanField(default=True)
    
    class Meta:
        ordering = ('-date_added',)

    class Meta:
        verbose_name = "Video"

    def get_content(self):
        return self.thumbnail_url
        
    def __unicode__(self):
        return self.description and self.description.replace('\n', ' ')\
          or self.embed_src[:40]

    @models.permalink
    def get_absolute_url(self):
        return ("video.view", (self.user.username, self.id))
    
    
class AutoLoginKey(models.Model):
    """AutoLoginKey objects makes it possible for a user to log in
    automatically without supplying a password as long as they
    supply a valid uuid.
    
    See the middleware for how this is being used
    """
    user = models.ForeignKey(User)
    uuid = models.CharField(max_length=128, db_index=True)
    date_added = models.DateTimeField('date added', default=datetime.now)
    
    def __unicode__(self):
        return "%s (%s)" % (self.uuid, self.user.username)
    
    @classmethod
    def get_or_create(self, user):
        try:
            return AutoLoginKey.objects.get(user=user)
        except AutoLoginKey.DoesNotExist:
            return AutoLoginKey.objects.create(user=user,
                                               uuid=str(uuid.uuid4()))
        
    @classmethod
    def find_user_by_uuid(self, uuid):
        try:
            return AutoLoginKey.objects.get(uuid=uuid).user
        except AutoLoginKey.DoesNotExist:
            return None
        
    
    
    
    
    
class KungfuPerson(models.Model):
    class Meta:
        verbose_name_plural = 'Kung fu people'

    
    NEWSLETTER_CHOICES = (('', 'Opt out'),
                          ('plain', 'Plain text'),
                          ('html', 'HTML'),
                          )
    
    user = models.ForeignKey(User, unique=True)
    bio = models.TextField(blank=True)
    styles = models.ManyToManyField(Style)
    club_membership = models.ManyToManyField(Club)
    what_is_kungfu = models.CharField(max_length=144, blank=True)

    # Location stuff - all location fields are required
    country = models.ForeignKey(Country)
    region = models.ForeignKey(Region, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_description = models.CharField(max_length=50)
    
    # Profile photo
    photo = models.ImageField(blank=True, upload_to='profiles')
    
    # default is 'html;, they can override that later if they want to unsubscribe
    # (possible values are ('', 'plain', 'html')
    newsletter = models.CharField(max_length=5, default='html',
                                  choices=NEWSLETTER_CHOICES,
                                  blank=True
                                 )

    # Stats
    profile_views = models.IntegerField(default=0)
    came_from = models.CharField(max_length=250, null=True, blank=True)
    
    objects = DistanceManager()

    def __unicode__(self):
        return unicode(self.user.get_full_name())
    
    @models.permalink
    def get_absolute_url(self):
        return ("person.view", (self.user.username,))
    
    def __repr__(self):
        return "<KungfuPerson: %r>" % self.user.username

    def get_nearest(self, num=5, within_range=20):
        #from time import time
        #t0=time()
        #r = self._get_nearest(num=num)
        #t1=time()
        #print "RESULT", (t1-t0)
        #
        #print r
        #t0=time()
        
        
        ##r = [p for (p, d) 
        ##     in KungfuPerson.objects.nearest_to((self.longitude, self.latitude),
        ##                                        number=num, within_range=within_range,
        ##                                        extra_where_sql='id<>%s' % self.id)]
        
        r = []
        people = KungfuPerson.objects.nearest_to((self.latitude, self.longitude),
                                                number=num, within_range=within_range,
                                                extra_where_sql='id<>%s' % self.id)
        for person, distance_miles in people:
            person.distance_miles = distance_miles
            r.append(person)
        
        #t1=time()
        #print "RESULT 2", (t1-t0)
        #print r
        #     
        #print "\n"
        
        return r
    
    def _get_nearest(self, num=5):
        "Returns the nearest X people, but only within the same continent"
        raise DeprecatedError, " use KungfuPerson.objects.nearest_to() instead"
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
    
    def get_person_upload_folder(self):
        
        try:
            temporary_upload_folder_base = settings.TEMPORARY_UPLOAD_FOLDER
        except AttributeError:
            from tempfile import gettempdir
            temporary_upload_folder_base = gettempdir()
            
        today = datetime.now()
        return os.path.join(temporary_upload_folder_base,
                            today.strftime('%Y'),
                            today.strftime('%b'),
                            self.user.username,
                            datetime.now().strftime('%d')
                        )
    
    def get_person_thumbnail_folder(self):
        return os.path.join(settings.MEDIA_ROOT, 'photos', 'upload-thumbnails', 
                            self.user.username)
    
    def get_photos(self):
        return Photo.objects.filter(user=self.user).order_by('-date_added').select_related()
    
    
    def get_same_club_people(self):
        """return a queryset of people who belong to the same club"""
        return []
        people = []
        for club in self.club_membership.all():
            for person in club.kungfuperson_set.exclude(id=self.id).select_related():
                if person not in people:
                    people.append(person)
        people.sort(lambda x,y: cmp(y.user.date_joined, x.user.date_joined))
        return people

    def get_same_style_people(self):
        """return a queryset of people who do the same style"""
        people = []
        for style in self.styles.all():
            for person in style.kungfuperson_set.exclude(id=self.id).select_related():
                if person not in people:
                    people.append(person)
        people.sort(lambda x,y: cmp(y.user.date_joined, x.user.date_joined))
        return people



def prowl_new_person(sender, instance, created, **__):
    description = "%s %s" % (instance.user.first_name, instance.user.last_name)
    site = Site.objects.get_current()
    description += "\nhttp://%s%s" % (site.domain, instance.get_absolute_url())
    if created:
        try:
            prowl("New person:",
                  description=description)
        except:
            try:
                print repr(description)
            except:
                pass
            logging.error("Unabled to prowl about new person",
                          exc_info=True)
            
post_save.connect(prowl_new_person, sender=KungfuPerson)

def _kungfuperson_saved(sender, instance, created, **__):
    for cache_key in ('all_people', 'people_count'):
        cache.delete(cache_key)
post_save.connect(_kungfuperson_saved, sender=KungfuPerson,
                  dispatch_uid="_kungfuperson_saved")

    
class CountrySite(models.Model):
    "Community sites for various countries"
    title = models.CharField(max_length = 100)
    url = models.URLField(max_length = 255)
    country = models.ForeignKey(Country)
    
    def __unicode__(self):
        return '%s <%s>' % (self.title, self.url)
   


class Recruitment(models.Model):
    """when one user recruits another user"""
    recruiter = models.ForeignKey(User, related_name='recruiter')
    recruited = models.ForeignKey(User, related_name='recruited')
    date_added = models.DateTimeField('date added', default=datetime.now)
    
    def __unicode__(self):
        return u"%s recruited %s" % (self.recruiter, self.recruited)
    
    
    
    
