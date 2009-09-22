# python
import logging
import os, md5, datetime
import re
from urlparse import urlparse
from PIL import Image
from cStringIO import StringIO
from urllib2 import HTTPError, URLError

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify, truncatewords
from django.template.loader import render_to_string
from django.conf import settings
from django.db import transaction
from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.core.paginator import Paginator


# project
from sorl.thumbnail.main import DjangoThumbnail, get_thumbnail_setting
from sorl.thumbnail.processors import dynamic_import, get_valid_options
thumbnail_processors = dynamic_import(get_thumbnail_setting('PROCESSORS'))

# app
from models import KungfuPerson, Country, User, Region, Club, Video, Style, \
  DiaryEntry, Photo, Recruitment
import utils
from utils import unaccent_string, must_be_owner, get_unique_user_cache_key, \
  get_previous_next, uniqify
from forms import SignupForm, LocationForm, ProfileForm, VideoForm, ClubForm, \
  StyleForm, DiaryEntryForm, PhotoUploadForm, ProfilePhotoUploadForm, \
  PhotoEditForm, NewsletterOptionsForm, CropForm
from data import get_all_items
from iplookup import getGeolocationByIP, getGeolocationByIP_cached

#from googlemaps import get_person_profile_static_map

from constants import MACHINETAGS_FROM_FIELDS, IMPROVIDERS_DICT, SERVICES_DICT

try:
    from django_static import slimfile, staticfile
except ImportError:
    from django_static.templatetags.django_static import slimfile, staticfile


ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60
ONE_DAY = ONE_HOUR * 24
ONE_WEEK = ONE_DAY * 7
ONE_YEAR = ONE_WEEK * 52

def set_cookie(response, key, value, expire=None):
    # http://www.djangosnippets.org/snippets/40/
    if expire is None:
        max_age = ONE_YEAR  #one year
    else:
        max_age = expire
    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + \
      datetime.timedelta(seconds=max_age), "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires,
                        domain=settings.SESSION_COOKIE_DOMAIN,
                        secure=settings.SESSION_COOKIE_SECURE or None)

def render(request, template, context_dict=None, **kwargs):
    return render_to_response(
        template, context_dict or {}, context_instance=RequestContext(request),
                              **kwargs
    )

def render_json(data):
    return HttpResponse(simplejson.dumps(data),
                        mimetype='application/javascript')
    

def index(request):
    
    # if a user is logged in, perhaps from oauth, but don't have a profile
    # then force them to get a profile
    if not request.user.is_anonymous() and not request.user.is_superuser:
        try:
            request.user.get_profile()
        except KungfuPerson.DoesNotExist:
            # they have to get a full profile
            from twitter.models import TwitterUser
            try:
                TwitterUser.objects.get(user=request.user)
                # exists, then use the twitter signup
                return HttpResponseRedirect(reverse('twitter_signup'))
            except TwitterUser.DoesNotExist:
                # normal signup
                return HttpResponseRedirect(reverse('signup'))
        
    cache_key = 'all_people'
    people = cache.get(cache_key)
    if people is None:
        people = KungfuPerson.objects.all().select_related().order_by('-id')
        cache.set(cache_key, people, ONE_WEEK)
    
    recent_people = people[:24]
    
    cache_key = 'people_count'
    people_count = cache.get(cache_key)
    if people_count is None:
        people_count = KungfuPerson.objects.all().count()
        cache.set(cache_key, people_count, ONE_WEEK)
    
    cache_key = 'clubs_recent_5'
    clubs = cache.get(cache_key)
    if clubs is None:
        clubs = Club.objects.all().order_by('-add_date')[:5]  # select_related()???
        cache.set(cache_key, clubs, ONE_WEEK)
        
    cache_key = 'styles_recent_5'
    styles = cache.get(cache_key)
    if styles is None:
        styles = Style.objects.all().order_by('-add_date')[:5] # select_related()???
        cache.set(cache_key, styles, ONE_WEEK)
    
    
    people_locations_json = _get_people_locations_json(people)
    
    unique_countries = uniqify([x.country for x in people],
                              lambda x: x.id)
    unique_countries.sort(lambda x,y: cmp(x.name.lower(), y.name.lower()))
    
    return render(request, 'index.html', {
        'people': people,
        'unique_countries': unique_countries,
        'people_locations_json': people_locations_json,
        'people_count': people_count,
        'styles': styles,
        'clubs': clubs,
        'recent_people': recent_people,
        'total_people': people_count,
    })

def _get_people_locations_json(people):
    # turn the list of people into a JSON string but only
    # have the user id and location
    people_locations = [dictify_person_details(x) for x in people]
    return simplejson.dumps(people_locations)

def dictify_person_details(person):
    _person_keys = settings.MAP_KEYS;
    return {_person_keys.get('username','username'): person.user.username,
            _person_keys.get('latitude','latitude'): person.latitude,
            _person_keys.get('longitude','longitude'): person.longitude}

def _get_person_location_json(person):
    return simplejson.dumps(dictify_person_details(person))

def about(request):
    return render(request, 'about.html', {
        'total_people': KungfuPerson.objects.count(),
        'countries': Country.objects.top_countries(),
    })

def about_new(request):
    return render(request, 'about_new.html')

def about_what(request):
    return render(request, 'about_what.html')


def recent(request):
    return render(request, 'recent.html', {
        'people': KungfuPerson.objects.all().select_related().order_by('-auth_user.date_joined')[:50],
        'api_key': settings.GOOGLE_MAPS_API_KEY,
    })

from django.contrib import auth
def login(request):
    if request.method != 'POST':
        return render(request, 'login.html', {
            'next': request.REQUEST.get('next', ''),
        })
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = auth.authenticate(username=username, password=password)
    
    if user is not None and user.is_active:
        auth.login(request, user)
        return HttpResponseRedirect(
            request.POST.get('next', '/%s/' % user.username)
        )
    else:
        return render(request, 'login.html', {
            'is_invalid': True,
            'username': username, # Populate form
            'next': request.REQUEST.get('next', ''),
        })


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')

def lost_password(request):
    username = request.POST.get('username', '')
    if username:
        try:
            try:
                person = KungfuPerson.objects.get(user__username__iexact=username)
            except KungfuPerson.DoesNotExist:
                person = KungfuPerson.objects.get(user__email__iexact=username)
        except KungfuPerson.DoesNotExist:
            return render(request, 'lost_password.html', {
                'message': 'That was not a valid username.'
            })
        username = person.user.username
        cache_key = 'password_recover_%s' % username.replace(' ','')
        
        if cache.get(cache_key) is not None:
            msg = "Recovery instructions already sent.\n"
            msg += "Please try again a bit later.\n"
            return HttpResponse(msg)
        
        path = utils.lost_url_for_user(username)
        from django.core.mail import send_mail
        import smtplib
        current_url = request.build_absolute_uri()
        body = render_to_string('recovery_email.txt', {
            'path': path,
            'person': person,
            'site_url': 'http://' + urlparse(current_url)[1],
            'PROJECT_NAME': settings.PROJECT_NAME,
                                                       
        })
        try:
            send_mail(
                      '%s password recovery' % settings.PROJECT_NAME,
                      body,
                settings.RECOVERY_EMAIL_FROM, [person.user.email],
                fail_silently=False
            )
        except smtplib.SMTPException:
            return render(request, 'lost_password.html', {
                'message': 'Could not e-mail you a recovery link.',
            })
        
        
        cache.set(cache_key, 1, 60)
        
        return render(request, 'lost_password.html', {
            'message': ('An e-mail has been sent to %s with instructions for '
                "recovering your password. Don't forget to check your spam "
                'folder!' % person.user.email)
        })
    return render(request, 'lost_password.html')

def lost_password_recover(request, username, days, hash):
    user = get_object_or_404(User, username=username)
    if utils.hash_is_valid(username, days, hash):
        user.backend='django.contrib.auth.backends.ModelBackend' 
        auth.login(request, user)
        return HttpResponseRedirect('/%s/password/' % username)
    else:
        return render(request, 'lost_password.html', {
            'message': 'That was not a valid account recovery link'
        })

@transaction.commit_on_success
def signup(request, initial_user=None):
    
    if not request.user.is_anonymous():
        try:
            request.user.get_profile()
            return HttpResponseRedirect('/')
        except KungfuPerson.DoesNotExist:
            pass
        
    if initial_user is None and request.method == 'POST' and \
      request.POST.get('initial_user_id'):
        initial_user = User.objects.get(pk=request.POST.get('initial_user_id'))

    all_clubs = [dict(name=x.name, url=x.url) for x in Club.objects.all()]
    all_clubs_js = simplejson.dumps(all_clubs)
    
    base_location = None
    
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        # if there is an initial user drop the password fields
        if initial_user:
            del form.fields['password1']
            del form.fields['password2']
            
        if form.is_valid():
            
            # First create the user
            if initial_user:
                user = initial_user
                username = user.username # needed later
                user.email = form.cleaned_data['email']
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.save()
            else:
                username = form.cleaned_data['username']
                creation_args = {
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                }
                if form.cleaned_data.get('password1'):
                    creation_args['password'] = form.cleaned_data['password1']
                    
                user = User.objects.create(**creation_args)
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.save()
                
            region = None
            if form.cleaned_data['region']:
                region = Region.objects.get(
                    country__iso_code = form.cleaned_data['country'],
                    code = form.cleaned_data['region']
                )
            
            # Now create the KungfuPerson
            person = KungfuPerson.objects.create(
                user = user,
                country = Country.objects.get(
                    iso_code = form.cleaned_data['country']
                ),
                region = region,
                latitude = form.cleaned_data['latitude'],
                longitude = form.cleaned_data['longitude'],
                location_description = form.cleaned_data['location_description']
            )
            
            if request.session.get('profile_image_url'):
                _download_profile_image(person, request.session.get('profile_image_url'))

            # and then add the style if provided
            style_name = form.cleaned_data['style']
            # in case they enter multiple styles
            for name in [x.strip() for x in style_name.split(',') if x.strip()]:
                slug = slugify(unaccent_string(name))
                #slug = name.strip().replace(' ', '-').lower()
                if name:
                    style = _get_or_create_style(name)
                    style.slug = slug
                    style.save()
                    person.styles.add(style)
                
            # and then add their club membership if provided
            url = form.cleaned_data['club_url'].strip()
            name = form.cleaned_data['club_name'].strip()
            slug = slugify(unaccent_string(name).replace('&','and'))
            #slug = name.strip().replace(' ', '-').lower()
            if url and name:
                club = _get_or_create_club(name, url=url)
                club.slug = slug[:50]
                club.save()
                person.club_membership.add(club)
                person.save()
            
            # make sure they get one of those new passwords
            if not initial_user:
                user.set_password(creation_args['password'])
                user.save()
            
            # use the cookie Google Analytics gives us
            utmz = request.COOKIES.get('__utmz')
            if utmz:
                try:
                    utmcsr = re.findall('utmcsr=([^\|]+)\|', utmz)[0]
                    utmccn = re.findall('utmccn=([^\|]+)\|', utmz)[0]
                    try:
                        utmcct = re.findall('utmcct=(.*?)$', utmz)[0]
                    except IndexError:
                        utmcct = ''
                    try:
                        utmcmd = re.findall('utmcmd=(.*?)$', utmz)[0]
                    except IndexError:
                        utmcmd = ''
                    if utmcsr not in ('(direct)',):
                        came_from = "%s,%s,%s %s" % (utmcsr, utmcct, utmcmd, utmccn)
                        person.came_from = came_from
                        person.save()
                    
                except:
                    import sys
                    type_, val, tb = sys.exc_info()
                    print "UTMZ", repr(utmz)
                    print "ERROR: %s: %s" % (type_, val)
                    import traceback
                    traceback.print_tb(tb)
                    logging.error("Unable to set came_from",
                                exc_info=True)
                    
            if request.session.get('recruiter'):
                # Note: request.session.get('recruiter') is the user ID
                recruiter = User.objects.get(id=request.session.get('recruiter'))
                if recruiter != user:
                    Recruitment.objects.create(recruiter=recruiter,
                                               recruited=user)
                    
            
            from django.contrib.auth import load_backend, login
            for backend in settings.AUTHENTICATION_BACKENDS:
                if user == load_backend(backend).get_user(user.pk):
                    user.backend = backend
            if hasattr(user, 'backend'):
                login(request, user)

            return HttpResponseRedirect('/%s/whatnext/' % username)
        else: print form.errors
    else:
        
        initial = {}
        if initial_user is not None:
            initial['initial_user_id'] = initial_user.id
            initial['username'] = initial_user.username
            if initial_user.first_name:
                initial['first_name'] = initial_user.first_name
            if initial_user.last_name:
                initial['last_name'] = initial_user.last_name
            if initial_user.email and initial_user.email != 'twitteruser@kungfupeople.com':
                initial['email'] = initial_user.email

        if request.META.get('REMOTE_ADDR',''):
            ip = request.META.get('REMOTE_ADDR')
            # debugging
            if settings.DEBUG and (ip == '127.0.0.1' or ip.startswith('192.168.')):
                from random import choice, randint
                ip = choice(['156.25.4.2','150.70.84.41','62.203.65.228','220.231.34.10',
                             '58.171.130.89','82.132.138.250',
                             '193.247.250.13','72.204.121.78','202.154.137.7',
                             '62.6.149.26','202.154.143.159','216.86.82.83'])
                if randint(1,10):
                    # pretend that sometimes we can't get the IP
                    ip = ''
                
            if ip and not (ip == '127.0.0.1' or ip.startswith('192.168.')):
                base_location = getGeolocationByIP_cached(ip)
                if base_location['lat'] == 0.0 and base_location['lng'] == 0.0:
                    # getGeolocationByIP_cached failed :(
                    base_location = None
            
            if base_location:
                try:
                    country = Country.objects.get(name__iexact=base_location['country'])
                    initial['country'] = country.iso_code
                    
                    if base_location.get('region') and base_location.get('city') and\
                      base_location.get('region').lower() != base_location.get('city').lower():
                        initial['location_description'] = "%s, %s" % \
                          (base_location['city'], base_location['region'])
                    elif base_location['city']:
                        initial['location_description'] = base_location['city']
                    initial['latitude'] = base_location['lat']
                    initial['longitude'] = base_location['lng']
                except Country.DoesNotExist:
                    # the lookup is duff
                    base_location = None
        
        form = SignupForm(initial=initial)
        
    return render(request, 'signup.html', {
        'form': form,
        'api_key': settings.GOOGLE_MAPS_API_KEY,
        'base_location': base_location,
        'all_clubs_js': all_clubs_js,
        'initial_user': initial_user,
    })

def whatnext(request, username):
    person = get_object_or_404(KungfuPerson, user__username=username)

    return render(request, 'whatnext.html', locals())


def diary_entry(request, username, slug):
    person = get_object_or_404(KungfuPerson, user__username = username)
    entry = get_object_or_404(DiaryEntry, slug=slug)
    user = request.user
    if not entry.is_public and not user == person.user:
        raise Http404("You're not authorised to view this page")
    
    photos = Photo.objects.filter(diary_entry=entry).order_by('-date_added')
    
    diary_entry_location_json = _get_person_location_json(entry)
    
    is_owner = request.user.username == username
    return render(request, 'diary_entry.html', locals())
    

def _download_profile_image(person, image_url):
    # save the image
    from urllib import urlopen
    image_content = urlopen(image_url).read()
    image = Image.open(StringIO(image_content))
    format = image.format
    format = format.lower().replace('jpeg', 'jpg')
    filename = md5.new(image_content).hexdigest() + '.' + format
    path = os.path.join(settings.MEDIA_ROOT, 'profiles', filename)
    # check that the dir of the path exists
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        try:
            os.mkdir(dirname)
        except IOError:
            raise IOError, "Unable to created the directory %s" % dirname
    open(path, 'w').write(image_content)
    person.photo = 'profiles/%s' % filename
    person.save()
    

def _get_or_create_club(name, url=None):
    assert name, "must have a club name"
    # search by name
    try:
        return Club.objects.get(name__iexact=name)
    except Club.DoesNotExist:
        pass
    
    if url:
        if not url.startswith('http'):
            url = 'http://' + url
        try:
            url_start = '://'.join(urlparse(url)[:2])
            return Club.objects.get(url__istartswith=url_start)
        except Club.DoesNotExist:
            pass
        
    # still here?!
    slug = slugify(unaccent_string(name).replace('&','and'))
    return Club.objects.create(url=url, name=name.strip(),
                               slug=slug.strip())

def _get_or_create_style(name):
    # search by name
    try:
        return Style.objects.get(name__iexact=name.strip())
    except Style.DoesNotExist:
        pass
        
    # still here?!
    return Style.objects.create(name=name)

import re
notalpha_re = re.compile('[^a-zA-Z0-9]')
def derive_username(nickname):
    nickname = notalpha_re.sub('', nickname)
    if not nickname:
        return ''
    base_nickname = nickname
    to_add = 1
    while True:
        try:
            KungfuPerson.objects.get(user__username = nickname)
        except KungfuPerson.DoesNotExist:
            break
        nickname = base_nickname + str(to_add)
        to_add += 1
    return nickname



@must_be_owner
def diary_entry_location_json(request, username, slug):
    person = get_object_or_404(KungfuPerson, user__username=username)
    diary_entry = get_object_or_404(DiaryEntry, slug=slug)
    
    data = {'country': diary_entry.country.iso_code,
            'location_description': diary_entry.location_description,
            'latitude': diary_entry.latitude,
            'longitude': diary_entry.longitude
            }
    return render_json(data)


class UploadError(Exception):
    pass

    

    

def swf_upload_test(request):
    if request.method == "POST":
        person = KungfuPerson.objects.all().order_by('?')[0]
        
        filename = request.POST['Filename']
        filedata = request.FILES['Filedata']
        
        upload_folder = person.get_person_upload_folder()
        
        def _mkdir(newdir):
            """works the way a good mkdir should :)
                - already exists, silently complete
                - regular file in the way, raise an exception
                - parent directory(ies) does not exist, make them as well
            """
            if os.path.isdir(newdir):
                pass
            elif os.path.isfile(newdir):
                raise OSError("a file with the same name as the desired " \
                            "dir, '%s', already exists." % newdir)
            else:
                head, tail = os.path.split(newdir)
                if head and not os.path.isdir(head):
                    _mkdir(head)
                if tail:
                    os.mkdir(newdir)
                    
        _mkdir(upload_folder)
        
        image_content = filedata.read()
        image = Image.open(StringIO(image_content))
        format = image.format
        format = format.lower().replace('jpeg', 'jpg')
        filename = md5.new(image_content).hexdigest() + '.' + format
        # Save the image
        path = os.path.join(upload_folder, filename)
        open(path, 'w').write(image_content)
        image.thumbnail((40, 40))
        thumbnail_folder = _get_person_thumbnail_folder(person)
        _mkdir(thumbnail_folder)
        thumbnail_path = os.path.join(thumbnail_folder, filename)
        image.save(thumbnail_path, image.format)
        return HttpResponse(thumbnail_path.replace(settings.MEDIA_ROOT, '/static'))
    else:
        return render(request, 'swf_upload_test.html', {})

    
        
        

#@must_be_owner # causes a 403! that's why it's commented out
def photo_upload_multiple_pre(request, username):
    """ used by the swfupload """
    person = get_object_or_404(KungfuPerson, user__username=username)
    
    # uploadify sends a POST but puts ?folder=xxx on the URL
    folder = request.GET.get('folder')
        
    if not request.method == 'POST':
        raise UploadError("Must be post")
    
    filename = request.POST['Filename']
    filedata = request.FILES['Filedata']
    
    upload_folder = person.get_person_upload_folder()

    def _mkdir(newdir):
        """works the way a good mkdir should :)
            - already exists, silently complete
            - regular file in the way, raise an exception
            - parent directory(ies) does not exist, make them as well
        """
        if os.path.isdir(newdir):
            pass
        elif os.path.isfile(newdir):
            raise OSError("a file with the same name as the desired " \
                        "dir, '%s', already exists." % newdir)
        else:
            head, tail = os.path.split(newdir)
            if head and not os.path.isdir(head):
                _mkdir(head)
            if tail:
                os.mkdir(newdir)
                
    _mkdir(upload_folder)
    
    image_content = filedata.read()
    image = Image.open(StringIO(image_content))
    format = image.format
    format = format.lower().replace('jpeg', 'jpg')
    filename = md5.new(image_content).hexdigest() + '.' + format
    # Save the image
    path = os.path.join(upload_folder, filename)
    open(path, 'w').write(image_content)
    
    image.thumbnail((60, 60))
    thumbnail_folder = person.get_person_thumbnail_folder()
    _mkdir(thumbnail_folder)
    thumbnail_path = os.path.join(thumbnail_folder, filename)
    image.save(thumbnail_path, image.format)
    
    return HttpResponse(thumbnail_path.replace(settings.MEDIA_ROOT, '/static'))


@must_be_owner
def photo_upload(request, username, prefer='multiple'):
    person = get_object_or_404(KungfuPerson, user__username=username)
    
    save_preference = False
    if request.method == "GET" and request.GET.get('prefer'):
        prefer = request.GET.get('prefer')
        if prefer not in ('single', 'multiple'):
            raise Http404("must be 'single' or 'multiple'")
        else:
            save_preference = prefer
    else:
        prefer = request.COOKIES.get('photo_upload', prefer)        
        
    upload_folder = person.get_person_upload_folder()
    
    if request.method == 'POST':
        filenames = []
        
        if prefer == 'multiple':
            form = PhotoUploadForm(request.POST)
            del form.fields['photo'] # not needed in multi-upload

            for f in os.listdir(upload_folder):
                if os.path.splitext(f.lower())[-1] in ('.jpg', '.gif', '.png'):
                    filenames.append(os.path.join(upload_folder, f))
        else:
            form = PhotoUploadForm(request.POST, request.FILES)


        if form.is_valid():
            user = person.user
            description = form.cleaned_data['description']
            region = None
            diary_entry = None
            upload_folder = None
            if prefer == 'single':
                photo = form.cleaned_data['photo']
                
                image_content = photo.read()
                format = Image.open(StringIO(image_content)).format
                format = format.lower().replace('jpeg', 'jpg')
                filename = md5.new(image_content).hexdigest() + '.' + format
                # Save the image
                path = os.path.join(settings.MEDIA_ROOT, 'photos', filename)
                # check that the dir of the path exists
                dirname = os.path.dirname(path)
                if not os.path.isdir(dirname):
                    try:
                        os.mkdir(dirname)
                    except IOError:
                        raise IOError, "Unable to created the directory %s" % dirname
                open(path, 'w').write(image_content)
                filenames = [path]
                
            for filepath in filenames:
                filename = os.path.basename(filepath)
                upload_folder = os.path.dirname(filepath)
                # Save the image
                path = os.path.join(settings.MEDIA_ROOT, 'photos', filename)
                # check that the dir of the path exists
                dirname = os.path.dirname(path)
                if not os.path.isdir(dirname):
                    try:
                        os.mkdir(dirname)
                    except IOError:
                        raise IOError, "Unable to created the directory %s" % dirname
                #open(path, 'w').write(image_content)
                os.rename(filepath, path)    
    
                if form.cleaned_data['diary_entry']:
                    diary_entry = form.cleaned_data['diary_entry']
                    if isinstance(diary_entry, int):
                        diary_entry = get_object_or_404(DiaryEntry, id=diary_entry)
                        if diary_entry.user != person.user:
                            # crazy paranoia
                            from django.forms import ValidationError
                            raise ValidationError("Not your entry")
    
                if form.cleaned_data['region']:
                    region = Region.objects.get(
                        country__iso_code = form.cleaned_data['country'],
                        code = form.cleaned_data['region']
                    ) 

                from django.core.files import File
                photo = Photo.objects.create(
                    user=user,
                    description=description,
                    photo=File(open(path, 'rb')),
                    diary_entry=diary_entry,
                    country=Country.objects.get(iso_code = form.cleaned_data['country']),
                    latitude=form.cleaned_data['latitude'],
                    longitude=form.cleaned_data['longitude'],
                    location_description=form.cleaned_data['location_description'],
                    region = region,
                    )

                    
            if upload_folder:
                if not os.listdir(upload_folder):
                    os.rmdir(upload_folder)
                
            if diary_entry:
                url = diary_entry.get_absolute_url()
            else:
                url = person.get_absolute_url()
            return HttpResponseRedirect(url)
    else:
        
        # make sure all uploaded photos are first deleted
        if os.path.isdir(upload_folder):
            for filename in os.listdir(upload_folder):
                if os.path.isfile(os.path.join(upload_folder, filename)):
                    os.remove(os.path.join(upload_folder, filename))
        
        initial = {'location_description': person.location_description,
                   'country': person.country.iso_code,
                   'latitude': person.latitude,
                   'longitude': person.longitude,
                  }
        form = PhotoUploadForm(initial=initial)
        
        diary_entries = []
        for entry in DiaryEntry.objects.filter(user=person.user
                                              ).order_by('-date_added')[:100]:
            title = entry.title
            if len(title) > 40:
                title = title[:40] + '...'
            title += entry.date_added.strftime(' (%d %b %Y)')
            diary_entries.append((entry.id, title))
            
        if diary_entries:
            diary_entries.insert(0, ('', ''))
            form.fields['diary_entry'].widget.choices = tuple(diary_entries)
        else:
            del form.fields['diary_entry']
            
    prefer_multiple = prefer == 'multiple'
    
    response = render(request, 'photo_upload_form.html', {
        'form': form,
        'person': person,
        'prefer_multiple': prefer == 'multiple'
    })
    
    if save_preference:
        set_cookie(response, 'photo_upload', save_preference,
                   expire=60*60*24*60)
        
    return response


@must_be_owner
def photo_edit(request, username, photo_id):
    person = get_object_or_404(KungfuPerson, user__username = username)
    photo = get_object_or_404(Photo, pk=photo_id)
    region = None
    page_title = "Edit your photo"
    button_value = "Save changes"
    
    diary_entries = []
    for entry in DiaryEntry.objects.filter(user=person.user
                                            ).order_by('-date_added')[:100]:
        title = entry.title
        if len(title) > 40:
            title = title[:40] + '...'
        title += entry.date_added.strftime(' (%d %b %Y)')
        diary_entries.append((entry.id, title))
        

    if request.method == 'POST':
        form = PhotoEditForm(request.POST)
        
        if diary_entries:
            diary_entries.insert(0, ('', ''))
            form.fields['diary_entry'].choices = tuple(diary_entries)
        else:
            del form.fields['diary_entry']
            
        if form.is_valid():  
            diary_entry = photo.diary_entry

            if form.cleaned_data['diary_entry']:
                diary_entry = DiaryEntry.objects.get(pk=form.cleaned_data['diary_entry'])

            if form.cleaned_data['region']:
                region = Region.objects.get(
                    country__iso_code = form.cleaned_data['country'],
                    code = form.cleaned_data['region']
                ) 

            photo.country = Country.objects.get(
                iso_code = form.cleaned_data['country']
            )
            photo.region = region
            photo.latitude = form.cleaned_data['latitude']
            photo.longitude = form.cleaned_data['longitude']
            photo.location_description = form.cleaned_data['location_description']
            photo.description = form.cleaned_data['description']
            photo.diary_entry = diary_entry
            photo.save()
            
            return HttpResponseRedirect(photo.get_absolute_url())
            #return HttpResponseRedirect('/%s/upload/done/' % username)
    else:
        initial = {
            'description': photo.description,
            'photo': photo,
            'country': photo.country.iso_code,
            'region': photo.region,
            'longitude': photo.longitude,
            'latitude': photo.latitude,
            'location_description': photo.location_description,
        }
        if photo.diary_entry:
            initial['diary_entry'] = photo.diary_entry.id
        form = PhotoEditForm(initial=initial)
        
        if diary_entries:
            diary_entries.insert(0, ('', ''))
            form.fields['diary_entry'].choices = tuple(diary_entries)
        else:
            del form.fields['diary_entry']
            
    return render(request, 'photo_upload_form.html', locals())

@must_be_owner
def photo_delete(request, username, photo_id):
    person = get_object_or_404(KungfuPerson, user__username = username)
    photo = get_object_or_404(Photo, pk=photo_id)
    page_title = "Delete this photo"

    photo.delete()

    return HttpResponseRedirect('/%s/upload/done/' % username)


@must_be_owner
def upload_profile_photo(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    if request.method == 'POST':
        form = ProfilePhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Figure out what type of image it is
            photo = request.FILES['photo']
            image_content = photo.read()
            image = Image.open(StringIO(image_content))
            format = image.format
            format = format.lower().replace('jpeg', 'jpg')
            filename = md5.new(image_content).hexdigest() + '.' + format
            # Save the image
            path = os.path.join(settings.MEDIA_ROOT, 'profiles', filename)
            # check that the dir of the path exists
            dirname = os.path.dirname(path)
            if not os.path.isdir(dirname):
                try:
                    os.mkdir(dirname)
                except IOError:
                    raise IOError, "Unable to created the directory %s" % dirname
            open(path, 'w').write(image_content)
            person.photo = 'profiles/%s' % filename
            person.save()
            
            # if the image is more than 10% away from being a square, encourage 
            # them to crop it
            (width, height) = image.size
            r = float(width)/height
            if r > 1.1 or r < 0.9:
                return HttpResponseRedirect(reverse("crop_profile_photo", 
                                                    args=(person.user.username,)))
            else:
                return HttpResponseRedirect(person.get_absolute_url())
    else:
        form = ProfilePhotoUploadForm()
    return render(request, 'upload_profile_photo.html', {
        'form': form,
        'person': person,
    })

#@must_be_owner
#def upload_done(request, username):
#    "Using a double redirect to try and stop back button from re-uploading"
    

def country(request, country_code):
    country = get_object_or_404(Country, iso_code=country_code.upper())
    people = KungfuPerson.objects.filter(country=country)
    
    people_locations_json = _get_people_locations_json(people)

    return render(request, 'country.html', {
        'country': country,
        'people': people,
        'people_locations_json': people_locations_json,
        'api_key': settings.GOOGLE_MAPS_API_KEY,
        'regions': country.top_regions(),
    })

def country_sites(request, country_code):
    country = get_object_or_404(Country, iso_code = country_code.upper())
    sites = PortfolioSite.objects.select_related().filter(
        contributor__country = country
    ).order_by('contributor')
    return render(request, 'country_sites.html', {
        'country': country,
        'sites': sites,
    })

def region(request, country_code, region_code):
    region = get_object_or_404(Region, 
        country__iso_code = country_code.upper(),
        code = region_code.upper()
    )
    return render(request, 'country.html', {
        'country': region,
        'api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def profile(request, username):
    try:
        person = KungfuPerson.objects.select_related().get(user__username=username)
    except KungfuPerson.DoesNotExist:
        raise Http404("No user by that username")
        
    clubs = person.club_membership.all().select_related()
    styles = person.styles.all().select_related()
    photos = Photo.objects.filter(user=person.user).order_by('-date_added')\
      .select_related()[:8]
    videos = Video.objects.filter(user=person.user).select_related()
    diary_entries_private = DiaryEntry.objects.filter(user=person.user)\
      .select_related().order_by('-date_added')[:5]
    diary_entries_public = DiaryEntry.objects.filter(user=person.user, is_public=True)\
      .select_related().order_by('-date_added')[:5]
    people_near = person.get_nearest(within_range=50)
    
    if '/competitions/' not in request.META.get('HTTP_REFERER', ''):
        cache_key = "profileviews-" + get_unique_user_cache_key(request.META)
        if cache.get(cache_key) is None:
            person.profile_views += 1 # Not bothering with transactions; only a stat
            person.save()
            cache.set(cache_key, 1, ONE_DAY)

    is_owner = request.user.username == username
    show_profile_views = is_owner and person.profile_views > 1
    
    if is_owner:
        # First assume that we don't have to pester the poor user
        # to upload a photo
        pester_first_photo = False
        if not person.photo:
            if request.GET.get('close_tip_first_photo'):
                if request.is_ajax():
                    response = HttpResponse('Hidden!')
                else:
                    response = HttpResponseRedirect(person.get_absolute_url())
                set_cookie(response, 'close_tip_photo', '1',
                           expire=60*60*24*3)
                return response
                           
            elif not request.COOKIES.get('close_tip_photo'):
                pester_first_photo = True
                
        # Same thing for the first diary entry
        pester_first_diary_entry = False
        if not diary_entries_private:
            if request.GET.get('close_tip_first_diary_entry'):
                if request.is_ajax():
                    response = HttpResponse('Hidden!')
                else:
                    response = HttpResponseRedirect(person.get_absolute_url())
                set_cookie(response, 'close_tip_diary_entry', '1',
                           expire=60*60*24*30)
                return response
                
            if not request.COOKIES.get('close_tip_diary_entry'):
                pester_first_diary_entry = True
                
        pester_first_style = False
        if not person.styles.all():
            if request.GET.get('close_tip_first_style'):
                if request.is_ajax():
                    response = HttpResponse('Hidden!')
                else:
                    response = HttpResponseRedirect(person.get_absolute_url())
                set_cookie(response, 'close_tip_style', '1',
                           expire=60*60*24*3)
                return response
                           
            elif not request.COOKIES.get('close_tip_style'):
                pester_first_style = True
            
    cache_key = 'same_club_people-%s' % person.user.username
    _same_club_info = cache.get(cache_key)
    if _same_club_info is None:
        same_club_people = []
        same_clubs = []
        for club in clubs:
            for same_club_person in club.kungfuperson_set.exclude(user=person.user):
                # found someone who also does this club
                if same_club_person not in same_club_people:
                    same_club_people.append(same_club_person)
                if club not in same_clubs:
                    same_clubs.append(club)
        cache.set(cache_key, (same_clubs, same_club_people),
                  ONE_WEEK)
    else:
        same_clubs, same_club_people = _same_club_info
    
    cache_key = 'same_style_people-%s' % person.user.username
    _same_style_info = cache.get(cache_key)
    if _same_style_info is None:
        same_style_people = []
        same_styles = []
        for style in styles:
            for same_style_person in style.kungfuperson_set.exclude(user=person.user):
                # found someone who also does this style
                if same_style_person not in same_style_people:
                    same_style_people.append(same_style_person)
                if style not in same_styles:
                    same_styles.append(style)
        cache.set(cache_key, (same_styles, same_style_people),
                  ONE_WEEK)
    else:
        same_styles, same_style_people = _same_style_info
        
    # Prep some SEO meta tags stuff
    meta_description = "%s %s, %s %s" % (person.user.first_name,
                                   person.user.last_name,
                                   person.location_description,
                                   person.country.name
                                  )
    
    if person.bio:
        meta_description += ", " + person.bio
        
    meta_keywords = []
    meta_keywords.append("%s %s" % (person.user.first_name, person.user.last_name))
    meta_keywords.append(person.location_description)
    meta_keywords.append(person.country.name)
    for club in clubs:
        meta_keywords.append(club.name)
    for style in styles:
        meta_keywords.append(style.name)
    meta_keywords = ','.join(meta_keywords)
    
    try:
        recruiter = Recruitment.objects.get(recruited=person.user).recruiter
        recruiter_profile = recruiter.get_profile()
    except Recruitment.DoesNotExist:
        pass
    
    recruited_users = Recruitment.objects.filter(recruiter=person.user)\
      .order_by('-add_date')
    recruited_people = [x.recruited.get_profile() for x in recruited_users]
    
    # for the world map
    people_locations_json = _get_people_locations_json(people_near)
    person_location_json = _get_person_location_json(person)
    
    
    return render(request, 'profile.html', locals())

def user_info_html(request, username, include_photo=False):
    """render a snippet of HTML about a person"""
    person = get_object_or_404(KungfuPerson, user__username=username)
    clubs = person.club_membership.all()
    styles = person.styles.all()
    
    return render(request, '_user-info.html', locals())


def wall(request):
    people = KungfuPerson.objects.all()
    return render(request, 'wall.html', locals())

def photo(request, username, photo_id):
    person = get_object_or_404(KungfuPerson, user__username=username)
    photo = get_object_or_404(Photo, id=photo_id)
    
    try:
        html_title = photo.description.splitlines()[0]
        meta_description = photo.description.replace('\n', '')
        html_title = truncatewords(html_title, 10)
        if photo.location_description:
            html_title += ', %s' % photo.location_description
        if photo.country:
            html_title += ', %s' % photo.country.name
    except IndexError:
        html_title = None
        
    # to figure out what photo comes next or previous we need to look at what
    # set this photo belong to. If this photo is a list of photos related to a
    # diary entry, then use that. Otherwise, assume that the photo is related 
    # to a user simply and work from that. 
    if photo.diary_entry:
        photo_set = Photo.objects.filter(diary_entry=photo.diary_entry)\
          .select_related()
    else:
        photo_set = Photo.objects.filter(user=photo.user).select_related()
    previous, next = get_previous_next(photo_set, photo)
    
    photo_location_json = _get_person_location_json(photo)
    
    is_owner = request.user.username == username
    return render(request, 'photo.html', locals())

def viewallphotos(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    photos = Photo.objects.filter(user=person.user).order_by('-date_added')

    return render(request, 'photos_all.html', {
        'person': person,
        'photos': photos,
        'is_owner': request.user.username == username,
    })

def club(request, name):
    club = get_object_or_404(Club, slug=name)
    people = members = KungfuPerson.objects.filter(club_membership=club)
    count = members.count()
    
    if '/competitions/' not in request.META.get('HTTP_REFERER', ''):
        cache_key = "clicks-club-" + get_unique_user_cache_key(request.META)
        if cache.get(cache_key) is None:
            club.clicks += 1 # Not bothering with transactions; only a stat
            club.save()
            cache.set(cache_key, 1, ONE_DAY)
    
    # for the world map
    people_locations_json = _get_people_locations_json(people)

    return render(request, 'club.html', locals())


def all_something(request, model, sort_by='name'):
    if sort_by not in ('date','name'):
        raise Http404("unrecognized sort-by")
    
    if model not in ('clubs','styles','people','photos'):
        raise Http404("unrecognized model")
    
    data = locals()
    current_url = request.build_absolute_uri()
    
    list_options = []
    
    if sort_by == 'date':
        _view_name = "all_something_by_date"
    else:
        _view_name = "all_something"
    for model_name in ('people','clubs','styles','photos'):
        url = reverse(_view_name, args=(model_name,))
        list_options.append(dict(label=model_name,
                                 url=url,
                                 active=current_url.endswith(url)
                            ))
    
    order_by_options = []
    
    url = reverse("all_something", args=(model,))
    order_by_options.append(dict(label='name',
                                 url=url,
                                 active=current_url.endswith(url)
                                 ))
    
    url = reverse("all_something_by_date", args=(model,))
    order_by_options.append(dict(label='date',
                                 url=url,
                                 active=current_url.endswith(url)
                                 ))
    
    data.update(dict(list_options=list_options,
                     order_by_options=order_by_options))
    
    data.update(get_all_items(model, sort_by))
    
    return render(request, 'all_something.html', data)
        

def style(request, name):
    style = get_object_or_404(Style, slug=name)
    people = KungfuPerson.objects.filter(styles=style).select_related()
    
    diaries = DiaryEntry.objects.filter(is_public=True,
                                        user__in=[x.id for x in people]).order_by('-date_added')
    count = people.count()
    
    club_ids = set()
    for person in people:
        club_ids.update([x.id for x in person.club_membership.all()])
    clubs = Club.objects.filter(id__in=list(club_ids)).select_related()

    if '/competitions/' not in request.META.get('HTTP_REFERER', ''):
        cache_key = "clicks-style-" + get_unique_user_cache_key(request.META)
        if cache.get(cache_key) is None:
            style.clicks += 1 # Not bothering with transactions; only a stat
            style.save()
            cache.set(cache_key, '1', ONE_DAY)
            
    # for the world map
    people_locations_json = _get_people_locations_json(people)
            
    return render(request, 'style.html', locals())


@must_be_owner
def edit_profile(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    try:
        example = KungfuPerson.objects.exclude(what_is_kungfu=u'').order_by('?')[0]
    except IndexError:
        example = None

    if request.method == 'POST':
        form = ProfileForm(request.POST, person=person)
        if form.is_valid():
            user = person.user             
            user.email = form.cleaned_data['email']
            person.bio = form.cleaned_data['bio']
            person.club_membership.url = form.cleaned_data['club_url']
            person.club_membership.name = form.cleaned_data['club_name']
            person.what_is_kungfu = form.cleaned_data['what_is_kungfu']
            user.save()
            person.save()
            return HttpResponseRedirect('/%s/' % username)
    else:
        initial = {
            'bio': person.bio,
            'what_is_kungfu': person.what_is_kungfu,
            'email': person.user.email,
        }
        form = ProfileForm(initial=initial, person=person)
    return render(request, 'edit_profile.html', {
        'form': form,
        'person': person,
        'example': example,
    })

@must_be_owner
def diary_entry_add(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    entries = DiaryEntry.objects.filter(user=person.user).order_by('-date_added')[:5]
    page_title = "Add a blog post"
    
    if request.method == 'POST':
        form = DiaryEntryForm(request.POST)
        if form.is_valid(): 
            user = person.user
            title = form.cleaned_data['title']
            content = form.cleaned_data['content']
            is_public = form.cleaned_data['is_public']
            slug = slugify(unaccent_string(title).replace('&','and')[:50])
            region = None

            if form.cleaned_data['region']:
                region = Region.objects.get(
                    country__iso_code = form.cleaned_data['country'],
                    code = form.cleaned_data['region']
                )

            if form.cleaned_data['country']:
                entry = DiaryEntry.objects.create(
                    user=user,
                    title=title,
                    content=content,
                    is_public=is_public,
                    slug=slug,
                    country=Country.objects.get(iso_code = form.cleaned_data['country']),
                    latitude=form.cleaned_data['latitude'],
                    longitude=form.cleaned_data['longitude'],
                    location_description=form.cleaned_data['location_description'],
                    region = region,
                    )

            else:
                entry = DiaryEntry.objects.create(
                    user=user,
                    title=title,
                    content=content,
                    is_public=is_public,
                    slug=slug, 
                    country=person.country,
                    latitude=person.latitude,
                    longitude=person.longitude,
                    location_description=person.location_description,
                    region=person.region,
                )

            
            return HttpResponseRedirect(entry.get_absolute_url())

    else:
        # figure out the initial location and country
        
        # by default, assume that the entry should be public
        is_public = True
        # look at the past ones
        count_public = count_not_public = 0
        for each in DiaryEntry.objects.filter(user=person.user).order_by('-date_added')[:10]:
            if each.is_public:
                count_public += 1
            else:
                count_not_public += 1
        if count_not_public > count_public:
            is_public = False
        
        initial = {'location_description': person.location_description,
                   'country': person.country.iso_code,
                   'latitude': person.latitude,
                   'longitude': person.longitude,
                   'is_public': is_public,
                  }
        form = DiaryEntryForm(initial=initial)
    return render(request, 'diary_entry_add.html', locals())


@must_be_owner
def diary_entry_edit(request, username, slug):
    person = get_object_or_404(KungfuPerson, user__username = username)
    entry = get_object_or_404(DiaryEntry, slug=slug, user=person.user)
    page_title = "Edit your blog post"

    if request.method == 'POST':
        form = DiaryEntryForm(request.POST)
        if form.is_valid():  
            entry.title = form.cleaned_data['title']
            entry.content = form.cleaned_data['content']
            entry.is_public = form.cleaned_data['is_public']
            entry.slug = entry.title.strip().replace(' ', '-').lower()
            if form.cleaned_data['region']:
                region = Region.objects.get(
                    country__iso_code = form.cleaned_data['country'],
                    code = form.cleaned_data['region']
                )
                entry.region = region
                
            if form.cleaned_data['country']:
                entry.country = Country.objects.get(iso_code=form.cleaned_data['country'])
                entry.location_description = form.cleaned_data['location_description']
                entry.latitude = form.cleaned_data['latitude']
                entry.longitude = form.cleaned_data['longitude']

            entry.save()
            #return HttpResponseRedirect('/%s/diary/%s/' % (username, entry.slug))
            return HttpResponseRedirect(entry.get_absolute_url())
    else:
        initial = {
            'title': entry.title,
            'content': entry.content,
            'is_public': entry.is_public,
            'location_description': entry.location_description,
            'country': entry.country.iso_code,
            'latitude': entry.latitude,
            'longitude': entry.longitude,
        }
        form = DiaryEntryForm(initial=initial)
    return render(request, 'diary_entry_add.html', locals())

@must_be_owner
def diary_entry_delete(request, username, slug):
    person = get_object_or_404(KungfuPerson, user__username=username)
    entry = get_object_or_404(DiaryEntry, slug=slug)
    user = person.user
    assert entry.user == user
    entry.delete()

    return HttpResponseRedirect('/%s/' % user.username)
    

@must_be_owner
def edit_club(request, username):
    person = get_object_or_404(KungfuPerson, user__username=username)
    clubs = person.club_membership.all()

    if request.method == 'POST':
        form = ClubForm(request.POST)
        if form.is_valid():        
            url = form.cleaned_data['club_url'] # not required field
            name = form.cleaned_data['club_name'] # required field
            # _get_or_create_club() takes care of creating slug if necessary
            club = _get_or_create_club(name, url=url)
            person.club_membership.add(club)
            person.save()
            cache_key = 'same_club_people-%s' % person.user.username
            cache.delete(cache_key)

            return HttpResponseRedirect('/%s/club/' % username)
        
        else:
            if form.non_field_errors():
                non_field_errors = form.non_field_errors()
            else:
                errors = form.errors
    else:
        form = ClubForm()
        current_club_ids = [x.id for x in clubs]
        all_clubs = [dict(name=x.name, url=x.url) for x in Club.objects.all()
                     if x.id not in current_club_ids]
        all_clubs_js = simplejson.dumps(all_clubs)
        del current_club_ids
        
    return render(request, 'edit_club.html', locals())

@must_be_owner
def delete_club_membership(request, username, clubname):
    person = get_object_or_404(KungfuPerson, user__username=username)
    user = request.user
    club = get_object_or_404(Club, slug=clubname)

    if not user == person.user:
        raise Http404("You're not authorised to perform this action")
    person.club_membership.remove(club)
    
    return HttpResponseRedirect('/%s/club/' % user.username)

@must_be_owner
def edit_style(request, username):
    person = get_object_or_404(KungfuPerson, user__username=username)
    styles = person.styles.all()

    if request.method == 'POST':
        form = StyleForm(request.POST)
        if form.is_valid():        
            name = form.cleaned_data['style_name'].strip()
            slug = name.strip().replace(' ', '-')
            slug = slugify(unaccent_string(slug))
            style = _get_or_create_style(name)
            style.slug = slug
            style.save()
            person.styles.add(style)
            person.save()
            cache_key = 'same_style_people-%s' % person.user.username
            cache.delete(cache_key)
            return HttpResponseRedirect('/%s/style/' % username)
    else:
        form = StyleForm()
        # generate a list of all styles for the javascript autocomplete.
        # TODO: If this starts to get too large (unlikely) consider
        # using AJAX instead.
        all_styles = [x.name for x in Style.objects.all()]
        all_styles_js = simplejson.dumps(all_styles)
        
    return render(request, 'edit_style.html', locals())

@must_be_owner
def delete_style(request, username, style):
    person = get_object_or_404(KungfuPerson, user__username=username)
    user = request.user
    style = get_object_or_404(Style, slug=style)

    if not user == person.user:
        raise Http404("You're not authorised to perform this action")
    person.styles.remove(style)
    
    return HttpResponseRedirect('/%s/style/' % user.username)
   



def video(request, username, video_id):
    person = get_object_or_404(KungfuPerson, user__username=username)
    video = get_object_or_404(Video, user=person.user, id=video_id)
    recent = Video.objects.all().order_by('-add_date').exclude(id=video.id)[:5]

    return render(request, 'videos.html', {
        'person': person,
        'video': video,
        'is_owner': request.user.username == username,
        'recent': recent,
    })
    

@must_be_owner
@transaction.commit_on_success
def add_video(request, username):
    person = get_object_or_404(KungfuPerson, user__username=username)
    if request.method == 'POST':
        form = VideoForm(request.POST)
        if form.is_valid():
            youtube_video_id = form.cleaned_data['youtube_video_id']
            embed_src = form.cleaned_data['embed_src']
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            thumbnail_url = form.cleaned_data['thumbnail_url']
            video = Video.objects.create(user=person.user,
                                         embed_src=embed_src,
                                         title=title.strip(),
                                         description=description.strip(),
                                         thumbnail_url=thumbnail_url,
                                        )
            return HttpResponseRedirect('/%s/' % username)
        else:
            print form.errors
    else:
        form = VideoForm()
    return render(request, 'add_video.html', {
        'form': form,
        'person': person,
        'user': person.user,
    })

@must_be_owner
def delete_video(request, username, pk):
    person = get_object_or_404(KungfuPerson, user__username=username)
    user = person.user
    video = get_object_or_404(Video, pk=pk)
    if not user == video.user:
        raise Http404("Not your video")
    
    video.delete()
    
    return HttpResponseRedirect('/%s/' % user.username)


@must_be_owner
def edit_account(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            person.save()
            return HttpResponseRedirect('/%s/' % username)
    else:
        form = AccountForm()
    return render(request, 'edit_account.html', {
        'form': form,
        'person': person,
        'user': person.user,
    })

@must_be_owner
def edit_password(request, username):
    user = get_object_or_404(User, username = username)
    p1 = request.POST.get('password1', '')
    p2 = request.POST.get('password2', '')
    if p1 and p2 and p1 == p2:
        user.set_password(p1)
        user.save()
        return HttpResponseRedirect('/%s/' % username)
    else:
        return render(request, 'edit_password.html')

@must_be_owner
def edit_location(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            region = None
            if form.cleaned_data['region']:
                region = Region.objects.get(
                    country__iso_code = form.cleaned_data['country'],
                    code = form.cleaned_data['region']
                )
            person.country = Country.objects.get(
                iso_code = form.cleaned_data['country']
            )
            person.region = region
            person.latitude = form.cleaned_data['latitude']
            person.longitude = form.cleaned_data['longitude']
            person.location_description = form.cleaned_data['location_description']
            person.save()
            return HttpResponseRedirect('/%s/' % username)
    else:
        initial = dict()
        if person.country:
            initial = dict(initial, country=person.country.iso_code)
        if person.location_description:
            initial = dict(initial, location_description=person.location_description)
        if person.latitude and person.longitude:
            initial = dict(initial, 
                           latitude=person.latitude,
                           longitude=person.longitude)
            
        form = LocationForm(initial=initial)
    return render(request, 'edit_location.html', {
        'form': form,
        'api_key': settings.GOOGLE_MAPS_API_KEY,
    })

from django.db.models import Q
import operator

def search_people(q):
    words = [w.strip() for w in q.split() if len(w.strip()) > 2]
    if not words:
        return []
    
    terms = []
    for word in words:
        terms.append(Q(
            user__username__icontains = word) | 
            Q(user__first_name__icontains = word) | 
            Q(user__last_name__icontains = word)
        )
    
    combined = reduce(operator.and_, terms)
    return KungfuPerson.objects.filter(combined).select_related().distinct()
    
def search(request):
    q = request.GET.get('q', '')
    has_badwords = [
        w.strip() for w in q.split() if len(w.strip()) in (1, 2)
    ]
    if q:
        people = search_people(q)
        return render(request, 'search.html', {
            'q': q,
            'results': people,
            'api_key': settings.GOOGLE_MAPS_API_KEY,
            'has_badwords': has_badwords,
        })
    else:
        return render(request, 'search.html')



def guess_club_name_json(request):
    club_url = request.GET.get('club_url')
    partial = request.GET.get('partial')
    
    if not club_url:
        return render_json(dict(error="no url"))

    club_url = club_url.strip()
    if not club_url.startswith('http'):
        if not club_url.startswith('file://'):
            club_url = 'http://' + club_url
        
    domain = urlparse(club_url)[1]
    data = {}
    
    if partial:
        try:
            club = Club.objects.get(url__istartswith=club_url)
            data = {'club_name': club.name, 'readonly': True}
        except Club.DoesNotExist:
            pass
        except Club.MultipleObjectsReturned:
            pass
        
    else:
        for club in Club.objects.filter(url__icontains=domain).order_by('-add_date'):
            data = {'club_name': club.name, 'readonly': True}
            # easy!
            return render_json(data)
        
    if partial:
        # don't go on the internet
        return render_json(data)
    
    # hmm, perhaps we need to download the HTML and scrape the <title> tag
    try:
        club_name_guess = _club_name_from_url(club_url, request)
        if club_name_guess:
            data['club_name'] = club_name_guess
    except HTTPError:
        data['error'] = u"Can't find that URL"
    except URLError:
        data['error'] = u"URL not recognized"
    
    
    return render_json(data)

def guess_nearby_clubs(request):
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    clubs = []
    
    return render_json(clubs)



def _club_name_from_url(url, request=None):
    if request:
        request_meta = request.META
    else:
        request_meta = {}
        
    html = utils.download_url(url, request_meta)
    
    title_regex = re.compile(r'<title>(.*?)</title>', re.I|re.M|re.DOTALL)
    try:
        title = title_regex.findall(html)[0].strip()
    except IndexError:
        return None
    
    try:
        title = unicode(title, 'utf-8')
    except UnicodeDecodeError:
        try:
            title = unicode(title, 'latin1')
        except UnicodeDecodeError:
            title = unicode(title, 'utf-8', 'ignore')
    
    parts = re.split('\s+-\s+', title)
    try:
        return parts[0]
    except IndexError:
        pass # :(
    
    return None
    


def guess_username_json(request):
    email = request.GET.get('email','').strip().lower()
    if not email:
        # AJAX call made wrong
        return render_json(dict(username=''))
    
    first_name = request.GET.get('first_name', '').strip().lower()
    last_name = request.GET.get('last_name', '').strip().lower()
    
    username = base_username = re.sub('[^\w]', '', email.split('@')[0])
    
    def is_taken(username):
        try:
            User.objects.get(username=username)
            return True
        except User.DoesNotExist:
            return False
        
    if is_taken(username):
        if not first_name and not last_name:
            # not a lot we can do at this point
            return render_json(dict(username=''))
        
        #for double-barrelled names, this removes the hyphen
        username = '%s%s' % (first_name, last_name.replace("-", ""))
        
    # getting really desperate!
    count = 2
    while is_taken(username):
        username = "%s%s" % (base_username, count)
        count += 1
        
    return render_json(dict(username=username))
 

@must_be_owner
def newsletter_options(request, username):
    person = get_object_or_404(KungfuPerson, user__username=username)
    
    if request.method == "POST":
        form = NewsletterOptionsForm(request.POST)
        if form.is_valid():
            newsletter = form.cleaned_data['newsletter']
            person.newsletter = newsletter
            person.save()
            return HttpResponseRedirect(person.get_absolute_url())
    else:
        form = NewsletterOptionsForm(initial=dict(newsletter=person.newsletter))

    return render(request, 'newsletter_options.html', locals())
        

def find_clubs_by_location_json(request):
    
    try:
        (latitude, longitude) = (float(request.GET['latitude']), 
                                 float(request.GET['longitude']))
    except (KeyError, ValueError):
        return render_json({'error':'Invalid parameters'})
    
    
    
    country = request.GET.get('country')
    location_description = request.GET.get('location_description')
    within_range = int(request.GET.get('within_range', 5)) # important!
    
    clubs = _find_clubs_by_location((latitude, longitude),
                                    country=country,
                                    location_description=location_description,
                                    within_range=within_range)
    
    if not clubs and location_description:
        clubs = _find_clubs_by_location((latitude, longitude),
                                        country=country,
                                        within_range=within_range)
        if not clubs:
            clubs = _find_clubs_by_location((latitude, longitude),
                                            country=country,
                                            within_range=within_range * 2)
            
            if not clubs:
                clubs = _find_clubs_by_location((latitude, longitude),
                                                country=country,
                                                within_range=within_range * 4)
                
    data = []
    for club in clubs:
        item = {'id': club.id,
                'url': club.url,
                'name': club.name,
                }
        data.append(item)
        
    return render_json(data)
                
            
    
    
def _find_clubs_by_location(location,
                            country=None, 
                            location_description=None,
                            within_range=10):

    extra_where_sql = []
    
    if country:
        if isinstance(country, basestring):
            if len(country) == 2:
                try:
                    country = Country.objects.get(iso_code=country.upper().strip())
                except Country.DoesNotExist:
                    pass
            else:
                try:
                    country = Country.objects.get(name=country)
                except Country.DoesNotExist:
                    try:
                        country = Country.objects.get(name__iexact=country.strip())
                    except Country.DoesNotExist:
                        pass
        # else, expect country to be an object
        extra_where_sql.append("country_id=%d" % country.id)
        
    if location_description:
        location_description = location_description.replace("'", "").\
          replace(";", "")
        extra_where_sql.append("UPPER(location_description)='%s'" % \
                               location_description.upper())
        
    # need to add extra where that checks if they are members of a club
    # XXX

    extra_where_sql = ' AND '.join(extra_where_sql)
    
    if type(location) is dict:
        if len(location) == 2:
            location = (location['latitude'], location['longitude'])
        elif len(location) == 4:
            location = (location['left'], location['upper'],
                        location['right'], location['lower'])
        else:
            raise ValueError("Invalid location parameter")
        
    if len(location) == 2:
        people = KungfuPerson.objects.nearest_to(location,
                                                 extra_where_sql=extra_where_sql,
                                                 within_range=within_range)
    elif len(location) == 4:
        people = KungfuPerson.objects.in_box(location,
                                             extra_where_sql=extra_where_sql)
    
    
    clubs = []

    for (person, distance) in people:
        for club in person.club_membership.all():
            if club not in clubs:
                clubs.append(club)
    return clubs


def zoom(request):
    """zoom() is about showing a map and when the user zooms in on a region
    it finds out what's in that region and updates a list.
    """
    people_count = KungfuPerson.objects.count()
    return render(request, 'zoom.html', locals())

def _get_zoom_content(left, upper, right, lower, request=None):

    clubs = []
    styles = []
    countries = []
    people = KungfuPerson.objects.in_box((left, upper, right, lower))
    
    for person in people:
        for club in person.club_membership.all():
            if club not in clubs:
                clubs.append(club)
        for style in person.styles.all():
            if style not in styles:
                styles.append(style)
                
        if person.country not in countries:
            countries.append(person.country)
        
    photos = Photo.objects.in_box((left, upper, right, lower))
    for photo in photos:
        if photo.country not in countries:
            countries.append(photo.country)
    
    diary_entries = DiaryEntry.objects.\
      in_box((left, upper, right, lower)).filter(is_public=True)
    for diary_entry in diary_entries:
        if diary_entry.country not in countries:
            countries.append(diary_entry.country)
    
    return locals()



def zoom_content(request):
    """zoom_content() just returns a limited block of html which is used to
    show a selection of clubs, styles, people, photos, etc. based on a zoomed
    region on a map. 
    """
    # Milano  
    # (right, lower) = 45.520661,9.100456 
    # Lyon,Bern corner  
    # (left, upper) = 46.789306,4.841881
    
    try:
        left = float(request.POST.get('left'))
        upper = float(request.POST.get('upper'))
        right = float(request.POST.get('right'))
        lower = float(request.POST.get('lower'))
    except (KeyError, ValueError, TypeError):
        logging.error("Invalid zoom", exc_info=True)
        return HttpResponse("Invalid zoom!")
    
    content_data = _get_zoom_content(left, upper, right, lower)
    
    return render(request, 'zoom-content.html', content_data)



def zoom_content_json(request):
    """same as zoom_content() but return it as a structure JSON string"""
    try:
        left = float(request.GET['left'])
        upper = float(request.GET['upper'])
        right = float(request.GET['right'])
        lower = float(request.GET['lower'])
    except (KeyError, ValueError, TypeError):
        logging.error("Invalid zoom", exc_info=True)
        return HttpResponse("Invalid zoom!")

    content_data = _get_zoom_content(left, upper, right, lower)
    
    def _jsonify_person(person):
        data = dict(url=person.get_absolute_url(),
                    fullname=unicode(person),
                    location_description=person.location_description,
                    iso_code=person.country.iso_code.lower(),
                    lat=person.latitude,
                    lng=person.longitude,
                   )
        if person.photo:
            thumbnail = DjangoThumbnail(person.photo, (60,60), opts=['crop'],
                                        processors=thumbnail_processors)
            data['thumbnail_url'] = thumbnail.absolute_url
            
            thumbnail = DjangoThumbnail(person.photo, (30,30), opts=['crop'],
                                        processors=thumbnail_processors)
            data['marker_thumbnail_url'] = thumbnail.absolute_url
        else:
            data['thumbnail_url'] = staticfile("/img/upload-a-photo-60.png")
            data['marker_thumbnail_url'] = staticfile("/img/upload-a-photo-30.png")
        clubs = []
        for club in person.club_membership.all():
            clubs.append({'name': club.name, 'url':club.get_absolute_url()})
        data['clubs'] = clubs
            
        return data
    
    def _jsonify_photo(photo):
        data = dict(url=photo.get_absolute_url(),
                    fullname=u"%s %s" % (photo.user.first_name, photo.user.last_name),
                    user_url=photo.user.get_profile().get_absolute_url(),
                    location_description=photo.location_description,
                    iso_code=photo.country.iso_code.lower(),
                    lat=photo.latitude,
                    lng=photo.longitude,
                    description=photo.description,
                   )
        
        thumbnail = DjangoThumbnail(photo.photo, (60,60), opts=['crop'], 
                                    processors=thumbnail_processors)
        data['thumbnail_url'] = thumbnail.absolute_url
        
        thumbnail = DjangoThumbnail(photo.photo, (30,30), opts=['crop'], 
                                    processors=thumbnail_processors)
        data['marker_thumbnail_url'] = thumbnail.absolute_url
        
        return data
    
    data = {}
    for person in content_data.get('people', []):
        if 'people' not in data:
            data['people'] = []
        
        data['people'].append(_jsonify_person(person))
        
    for club in content_data.get('clubs', []):
        if 'clubs' not in data:
            data['clubs'] = []
        data['clubs'].append(dict(url=club.get_absolute_url(),
                                  name=club.name))
        
    for style in content_data.get('styles', []):
        if 'styles' not in data:
            data['styles'] = []
        data['styles'].append(dict(url=style.get_absolute_url(),
                                   name=style.name))
        
    for photo in content_data.get('photos', []):
        if 'photos' not in data:
            data['photos'] = []
        
        data['photos'].append(_jsonify_photo(photo))
        
    for diary_entry in content_data.get('diary_entries', []):
        if 'diary_entries' not in data:
            data['diary_entries'] = []
        
        data['diary_entries'].append(dict(url=diary_entry.get_absolute_url(),
                                          title=diary_entry.title))
        
        
    for country in content_data.get('countries', []):
        if 'countries' not in data:
            data['countries'] = []
        
        data['countries'].append(dict(url=country.get_absolute_url(),
                                      title=country.name))        

    return render_json(data)


@must_be_owner
def crop_profile_photo(request, username):
    person = get_object_or_404(KungfuPerson, user__username=username)
    
    if not person.photo:
        return HttpResponseRedirect(reverse("upload_profile_photo",
                                           args=(username,)))
    
    photo = person.photo
    
    if request.GET.get('undo'):
        if not request.session.get('old_profile_path'):
            return HttpResponse("Old profile photo does not exist any more")
        
        person.photo = request.session['old_profile_path']
        person.save()
        return HttpResponseRedirect(reverse("crop_profile_photo",
                                           args=(username,)))
    
    image = Image.open(StringIO(photo.read()))

    width, height = image.size

    # but on the cropping page we'll show it as 500x500
    if height > width:
        width = 500 * width / height
        height = 500
    else:
        height = 500 * height / width
        width = 500

    if request.method == "POST":
        form = CropForm(request.POST)
        if form.is_valid():
            image = image.resize((width, height))
            image = image.crop((form.cleaned_data['x1'],
                                form.cleaned_data['y1'],
                                form.cleaned_data['x2'],
                                form.cleaned_data['y2']))
            old_path = photo.path
            ext = os.path.splitext(old_path)[-1]
            filename = md5.new(image.tostring()).hexdigest() + ext
            new_path = os.path.join(os.path.dirname(old_path),
                                    filename)

            image.save(new_path, image.format)
            person.photo = new_path.replace(settings.MEDIA_ROOT+'/', '')
            person.save()

            request.session['old_profile_path'] = old_path

        return HttpResponseRedirect(person.get_absolute_url())
    
    
    # set_select is about selecting a preselect box on the image that 
    # selects the maximum square possible. 
    # If the picture is a portrait, x1 and x2 should be 0 and image-width
    if height > width:
        # round one pixel in
        x1, x2 = 1, width - 1
        y1 = height/2 - width/2
        y2 = y1 + width
    else:
        y1, y2 = 1, height - 1
        x1 = width/2 - height/2
        x2 = x1 + height
        
    set_select_box = [x1, y1, x2, y2]
    
    form = CropForm(initial=dict(w=width, h=height,
                                 x1=set_select_box[0],
                                 y1=set_select_box[1],
                                 x2=set_select_box[2],
                                 y2=set_select_box[3],
                                ))
    
    
    return render(request, 'crop-profile-photo.html', locals())
    

def tinymce_filebrowser(request):
    type_ = request.GET.get('type') # needed?
    url = request.GET.get('url')
    if request.user and not request.user.is_anonymous():
        photos = Photo.objects.filter(user=request.user)
        
    return render(request, 'tinymce_filebrowser.html', locals())


# view function suffixed with _html to indicate that it's returning
# just a limited chunk of html
def nav_html(request):
    """return the piece of HTML that shows the nav,
    i.e. the content inside the tag <div id="nav"></div>
    """
    return render(request, '_nav.html', dict())


from youtube import YouTubeVideoError, get_youtube_video_by_id

def get_youtube_video_by_id_json(request):
    video_id = request.GET.get('video_id')
    if not video_id:
        raise ValueError("No video URL or ID")
    
    try:
        data = get_youtube_video_by_id(video_id)
    except YouTubeVideoError, msg:
        return render_json(dict(error=str(msg)))
    
    return render_json(data)

def runway(request):
    return render(request, 'runway.html', locals())

def runway_data_js(request):
    cache_key = 'runway_data_js'
    js = cache.get(cache_key)
    js=None
    if js is None:
        
        def get_person_subtitle(person):
            return ""
            subtitle = "%s, %s\n" % (person.location_description,
                                     person.country.name)
            clubs = [x.name for x in person.club_membership.all()]
            if len(clubs) == 1:
                subtitle += "Club: %s\n" % clubs[0]
            elif clubs:
                subtitle += "Clubs: %s\n" % ', '.join(clubs)
                
            styles = [x.name for x in person.styles.all()]
            if len(styles) == 1:
                subtitle += "Style: %s\n" % styles[0]
            elif styles:
                subtitle += "Styles: %s\n" % ', '.join(styles)
            
            return subtitle
            
        def get_person_title(person):
            return person.user.get_full_name()
        
        root_url = 'http://%s' % urlparse(request.build_absolute_uri())[1]
        people = KungfuPerson.objects.exclude(photo='').order_by('user__date_joined').select_related()
        records = []
        for person in people:
            thumbnail = DjangoThumbnail(person.photo, (200,200), opts=['crop'],
                                        processors=thumbnail_processors)
            thumbnail_url = thumbnail.absolute_url
            if thumbnail_url.startswith('/'):
                thumbnail_url = root_url + thumbnail_url
            data = dict(image=thumbnail_url,
                        title=get_person_title(person),
                        subtitle=get_person_subtitle(person),
                        username=person.user.username,
                        url=person.get_absolute_url())
            records.append(data)
            
        js = 'var RUNWAY_RECORDS=%s;\n' % simplejson.dumps(records)
        cache.set(cache_key, js, 60*60)# how many seconds?
    
    return HttpResponse(js, mimetype="text/javascript")
    
def crossdomain_xml(request):
    domain = "*"
    #print request.META.keys() # referer?
    xml = '<?xml version="1.0"?>\n'\
          '<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/'\
          'dtds/cross-domain-policy.dtd">\n'\
          """<cross-domain-policy>
           <allow-access-from domain="%s" />
          </cross-domain-policy>""" % domain
    xml = xml.strip()
    
    return HttpResponse(xml, mimetype="application/xml")
    
