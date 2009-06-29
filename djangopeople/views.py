import re
from urlparse import urlparse
from django.http import Http404, HttpResponse, HttpResponseRedirect, \
    HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string
from models import KungfuPerson, Country, User, Region, Club, Video, Style, DiaryEntry, Photo
import utils
from utils import unaccent_string
from forms import SignupForm, LocationForm, ProfileForm, VideoForm, ClubForm, StyleForm, DiaryEntryForm, PhotoUploadForm, ProfilePhotoUploadForm, PhotoEditForm
from constants import MACHINETAGS_FROM_FIELDS, IMPROVIDERS_DICT, SERVICES_DICT
from django.conf import settings
from django.db import transaction
import os, md5, datetime
from PIL import Image
from cStringIO import StringIO
from django.utils import simplejson
from urllib2 import HTTPError, URLError

def render(request, template, context_dict=None):
    return render_to_response(
        template, context_dict or {}, context_instance=RequestContext(request)
    )

def render_json(data):
    return HttpResponse(simplejson.dumps(data),
                        mimetype='application/javascript')
    
@utils.simple_decorator
def must_be_owner(view):
    def inner(request, *args, **kwargs):
        if not request.user or request.user.is_anonymous() \
            or request.user.username != args[0]:
            return HttpResponseForbidden('Not allowed')
        return view(request, *args, **kwargs)
    return inner

def index(request):
    recent_people = list(KungfuPerson.objects.all().select_related().order_by('-id')[:100])
    try:
        definition = KungfuPerson.objects.exclude(what_is_kungfu='').order_by('?')[:1].get()
    except KungfuPerson.DoesNotExist:
        definition = None
    clubs = Club.objects.all().order_by('-add_date')[:5]
    photos = Photo.objects.all().order_by('-date_added')[:5]
    styles = Style.objects.all().order_by('-add_date')[:5]
    your_person = None
    if request.user and not request.user.is_anonymous():
        your_person = request.user.get_profile()
    return render(request, 'index.html', {
        'recent_people': recent_people,
        'your_person': your_person,
        'photos': photos,
        'styles': styles,
        'definition': definition,
        'clubs': clubs,
        'recent_people_limited': recent_people[:4],
        'total_people': KungfuPerson.objects.count(),
        'total_videos': Video.objects.filter(approved=True).count(),
        'total_chris': User.objects.filter(first_name__startswith='Chris').count(),
        'api_key': settings.GOOGLE_MAPS_API_KEY,
    })

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
            person = KungfuPerson.objects.get(user__username = username)
        except KungfuPerson.DoesNotExist:
            return render(request, 'lost_password.html', {
                'message': 'That was not a valid username.'
            })
        path = utils.lost_url_for_user(username)
        from django.core.mail import send_mail
        import smtplib
        body = render_to_string('recovery_email.txt', {
            'path': path,
            'person': person,
        })
        try:
            send_mail(
                'Django People account recovery', body,
                settings.RECOVERY_EMAIL_FROM, [person.user.email],
                fail_silently=False
            )
        except smtplib.SMTPException:
            return render(request, 'lost_password.html', {
                'message': 'Could not e-mail you a recovery link.',
            })
        return render(request, 'lost_password.html', {
            'message': ('An e-mail has been sent with instructions for '
                "recovering your account. Don't forget to check your spam "
                'folder!')
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
def signup(request):
    if not request.user.is_anonymous():
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            # First create the user
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

            # and then add the style if provided
            name = form.cleaned_data['style']
            slug = name.strip().replace(' ', '-').lower()
            if name:
                style = _get_or_create_style(name)
                style.slug = slug
                style.save()
                person.styles.add(style)
            
            # and then add their club membership if provided
            url = form.cleaned_data['club_url']
            name = form.cleaned_data['club_name']
            slug = slugify(unaccent_string(name))
            #slug = name.strip().replace(' ', '-').lower()
            if url and name:
                club = _get_or_create_club(url, name)
                club.slug = slug
                club.save()
                person.club_membership.add(club)
                person.save()
            
            # make sure they get one of those new passwords
            user.set_password(creation_args['password'])
            user.save()
            
            from django.contrib.auth import load_backend, login
            for backend in settings.AUTHENTICATION_BACKENDS:
                if user == load_backend(backend).get_user(user.pk):
                    user.backend = backend
            if hasattr(user, 'backend'):
                login(request, user)

            return HttpResponseRedirect('/%s/whatnext/' % username)
        else: print form.errors
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {
        'form': form,
        'api_key': settings.GOOGLE_MAPS_API_KEY,
    })

def whatnext(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)

    return render(request, 'whatnext.html', locals())


def diary_entry(request, username, slug):
    person = get_object_or_404(KungfuPerson, user__username = username)
    entry = get_object_or_404(DiaryEntry, slug=slug)
    user = request.user
    if not entry.is_public and not user == person.user:
        raise Http404("You're not authorised to view this page")
    
    photos = Photo.objects.filter(diary_entry=entry).order_by('-date_added')

    return render(request, 'diary_entry.html', {        
        'is_owner': request.user.username == username,
        'person': person,
        'photos': photos,
        'entry': entry,
        'user': user,
    })
    

def _get_or_create_club(url, name):
    if url:
        if not url.startswith('http'):
            url = 'http://' + url
        try:
            url_start = '://'.join(urlparse(url)[:2])
            return Club.objects.get(url__istartswith=url_start)
        except Club.DoesNotExist:
            pass
        
    if name:
        # search by name
        try:
            return Club.objects.get(name__iexact=name)
        except Club.DoesNotExist:
            pass
    
    # still here?!
    if name:
        slug = slugify(unaccent_string(name))
    else:
        slug = ''
    return Club.objects.create(url=url, name=name,
                               slug=slug)

def _get_or_create_style(name):
    if name:
        # search by name
        try:
            return Style.objects.get(name__iexact=name)
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
def photo_upload(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = person.user
            description = form.cleaned_data['description']
            photo = form.cleaned_data['photo']
            region = None
            diary_entry = None
            # Figure out what type of image it is
            photo = request.FILES['photo']
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

            if form.cleaned_data['country']:
                photo = Photo.objects.create(
                    user=user,
                    description=description,
                    photo=photo,
                    diary_entry=diary_entry,
                    country=Country.objects.get(iso_code = form.cleaned_data['country']),
                    latitude=form.cleaned_data['latitude'],
                    longitude=form.cleaned_data['longitude'],
                    location_description=form.cleaned_data['location_description'],
                    region = region,
                    )

            else:
                photo = Photo.objects.create(
                    user=user,
                    description=description,
                    photo=photo,
                    diary_entry=diary_entry,
                    country=person.country,
                    latitude=person.latitude,
                    longitude=person.longitude,
                    location_description=person.location_description,
                    region=person.region,
                )
            
            if diary_entry:
                url = diary_entry.get_absolute_url()
            else:
                url = '/%s/upload/done/' % username
            return HttpResponseRedirect(url)
    else:
        
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
            form.fields['diary_entry'].widget.choices.extend(diary_entries)
        else:
            del form.fields['diary_entry']
            
    return render(request, 'photo_upload_form.html', {
        'form': form,
        'person': person,
    })


@must_be_owner
def photo_edit(request, username, photo_id):
    person = get_object_or_404(KungfuPerson, user__username = username)
    photo = get_object_or_404(Photo, pk=photo_id)
    region = None
    page_title = "Edit your photo"
    button_value = "Save changes"

    if request.method == 'POST':
        form = PhotoEditForm(request.POST)
        if form.is_valid():  
            diary_entry = photo.diary_entry

            if form.cleaned_data['diary_entry']:
                diary_entry = form.cleaned_data['diary_entry']

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

            return HttpResponseRedirect('/%s/upload/done/' % username)
    else:
        initial = {
            'description': photo.description,
            'photo': photo,
            'diary_entry': photo.diary_entry,
            'country': photo.country.iso_code,
            'region': photo.region,
            'longitude': photo.longitude,
            'latitude': photo.latitude,
            'location_description': photo.location_description,
        }
        form = PhotoEditForm(initial=initial)
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
            format = Image.open(StringIO(image_content)).format
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
            return HttpResponseRedirect('/%s/upload/done/' % username)
    else:
        form = ProfilePhotoUploadForm()
    return render(request, 'upload_profile_photo.html', {
        'form': form,
        'person': person,
    })

@must_be_owner
def upload_done(request, username):
    "Using a double redirect to try and stop back button from re-uploading"
    return HttpResponseRedirect('/%s/' % username)

def country(request, country_code):
    country = get_object_or_404(Country, iso_code = country_code.upper())
    people = KungfuPerson.objects.filter(country = country)

    return render(request, 'country.html', {
        'country': country,
        'people': people,

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
    person = get_object_or_404(KungfuPerson, user__username = username)
    clubs = person.club_membership.all()
    styles = person.styles.all()
    photos = Photo.objects.filter(user=person.user)
    videos = Video.objects.filter(user=person.user)
    diary_entries_private = DiaryEntry.objects.filter(user=person.user)
    diary_entries_public = DiaryEntry.objects.filter(user=person.user, is_public=True)
    person.profile_views += 1 # Not bothering with transactions; only a stat
    person.save()
    
    
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
    for club in person.club_membership.all():
        meta_keywords.append(club.name)
    for style in person.styles.all():
        meta_keywords.append(style.name)
   
    return render(request, 'profile.html', {
        'person': person,
        'styles': styles,
        'photos': photos,
        'diary_entries_private': diary_entries_private,
        'diary_entries_public': diary_entries_public,
        'clubs': clubs,
        'api_key': settings.GOOGLE_MAPS_API_KEY,
        'is_owner': request.user.username == username,
        'meta_description': meta_description,
        'meta_keywords': ','.join(meta_keywords),
    })

def photo(request, username, photo_id):
    person = get_object_or_404(KungfuPerson, user__username = username)
    photo = get_object_or_404(Photo, id=photo_id)

    return render(request, 'photo.html', {
        'person': person,
        'photo': photo,
        'is_owner': request.user.username == username,
    })

def club(request, name):
    club = get_object_or_404(Club, slug=name)
    members = KungfuPerson.objects.filter(club_membership=club)
    count = members.count()

    return render(request, 'club.html', locals())

def style(request, name):
    style = get_object_or_404(Style, slug=name)
    people = KungfuPerson.objects.filter(styles=style)
    diaries = DiaryEntry.objects.filter(user__in=[x.id for x in people]).order_by('-date_added')
    count = people.count()

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
    page_title = "Add a diary entry"
    
    if request.method == 'POST':
        form = DiaryEntryForm(request.POST)
        if form.is_valid(): 
            user = person.user
            title = form.cleaned_data['title']
            content = form.cleaned_data['content']
            is_public = form.cleaned_data['is_public']
            slug = slugify(unaccent_string(title)[:50])
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
    page_title = "Edit a diary entry"

    if request.method == 'POST':
        form = DiaryEntryForm(request.POST)
        if form.is_valid():  
            entry.title = form.cleaned_data['title']
            entry.content = form.cleaned_data['content']
            entry.is_public = form.cleaned_data['is_public']
            entry.slug = entry.title.strip().replace(' ', '-').lower()
            entry.save()
            #return HttpResponseRedirect('/%s/diary/%s/' % (username, entry.slug))
            return HttpResponseRedirect(entry.get_absolute_url())
    else:
        initial = {
            'title': entry.title,
            'content': entry.content,
            'is_public': entry.is_public,
            'location_description': person.location_description,
            'country': person.country.iso_code,
            'latitude': person.latitude,
            'longitude': person.longitude,
        }
        form = DiaryEntryForm(initial=initial)
    return render(request, 'diary_entry_add.html', locals())

@must_be_owner
def diary_entry_delete(request, username, slug):
    person = get_object_or_404(KungfuPerson, user__username = username)
    entry = get_object_or_404(DiaryEntry, slug=slug)
    user = person.user
    
    entry.delete()

    return HttpResponseRedirect('/%s/' % user.username)

    

@must_be_owner
def edit_club(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    clubs = person.club_membership.all()

    if request.method == 'POST':
        form = ClubForm(request.POST)
        if form.is_valid():        
            url = form.cleaned_data['club_url']
            name = form.cleaned_data['club_name']
            slug = name.strip().replace(' ', '-').lower()
            if url or name:
                club = _get_or_create_club(url, name)
                club.slug = slug
                club.save()
                person.club_membership.add(club)
                person.save()
                return HttpResponseRedirect('/%s/club/' % username)
    else:
        form = ClubForm()
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
    person = get_object_or_404(KungfuPerson, user__username = username)
    styles = person.styles.all()

    if request.method == 'POST':
        form = StyleForm(request.POST)
        if form.is_valid():        
            name = form.cleaned_data['style_name']
            slug = name.strip().replace(' ', '-').lower()
            if name:
                style = _get_or_create_style(name)
                style.slug = slug
                style.save()
                person.styles.add(style)
                person.save()
                return HttpResponseRedirect('/%s/style/' % username)
    else:
        form = StyleForm()
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
   



def videos(request, username):
    person = get_object_or_404(KungfuPerson, user__username=username)
    videos = Video.objects.filter(user=person.user)
    if not (request.user and request.user.username == username):
        your_videos = False
        # you're not watching your own videos
        videos = videos.filter(approved=True)
    else:
        your_videos = True

    return render(request, 'videos.html', {
        'person': person,
        'videos': videos,
        'is_owner': request.user.username == username,
        'your_videos': your_videos,
    })
    

@must_be_owner
def add_video(request, username):
    person = get_object_or_404(KungfuPerson, user__username=username)
    if request.method == 'POST':
        form = VideoForm(request.POST)
        if form.is_valid():
            embed_src = form.cleaned_data['embed_src']
            description = form.cleaned_data['description']
            video = Video.objects.create(user=person.user,
                                         embed_src=embed_src,
                                         description=description.strip())
            return HttpResponseRedirect('/%s/' % username)
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
    
    return HttpResponseRedirect('/%s/videos/' % user.username)


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
    if not club_url:
        return render_json(dict(error="no url"))

    club_url = club_url.strip()
    if not club_url.startswith('http'):
        if not club_url.startswith('file://'):
            club_url = 'http://' + club_url
        
    domain = urlparse(club_url)[1]
    data = {}
    
    for club in Club.objects.filter(url__icontains=domain).order_by('-add_date'):
        data = {'club_name': club.name, 'readonly': True}
        # easy!
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
        print html
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
    email = request.GET.get('email')
    first_name = request.GET.get('first_name')
    last_name = request.GET.get('last_name')
    
    username = base_username = email.split('@')[0].strip().lower().replace('.','')
    
    def is_taken(username):
        try:
            User.objects.get(username=username)
            return True
        except User.DoesNotExist:
            return False
    if is_taken(username):
        #for double-barrelled names, this removes the hyphen
        username = first_name.strip().lower() + '' + last_name.strip().replace("-", "").lower()
        
    count = 2
    while is_taken(username):
        username = "%s%s" % (base_username, count)
        count += 1
        
    return render_json(dict(username=username))
   
