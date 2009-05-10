from django.http import Http404, HttpResponse, HttpResponseRedirect, \
    HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from models import KungfuPerson, Country, User, Region
import utils
from forms import SignupForm, PhotoUploadForm, \
    BioForm, LocationForm, FindingForm, AccountForm
from constants import MACHINETAGS_FROM_FIELDS, IMPROVIDERS_DICT, SERVICES_DICT
from django.conf import settings
from django.db import transaction
import os, md5, datetime
from PIL import Image
from cStringIO import StringIO
from django.utils import simplejson

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
    return render(request, 'index.html', {
        'recent_people': recent_people,
        'recent_people_limited': recent_people[:4],
        'total_people': KungfuPerson.objects.count(),
        'total_chris': User.objects.filter(first_name__startswith='Chris').count(),
        'api_key': settings.GOOGLE_MAPS_API_KEY,
        'countries': Country.objects.top_countries(),
    })

def about(request):
    return render(request, 'about.html', {
        'total_people': KungfuPerson.objects.count(),
        'countries': Country.objects.top_countries(),
    })

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
                bio = form.cleaned_data['bio'],
                style = form.cleaned_data['style'],
                personal_url = form.cleaned_data['personal_url'],
                club_url = form.cleaned_data['club_url'],
                club_name = form.cleaned_data['club_name'],
                country = Country.objects.get(
                    iso_code = form.cleaned_data['country']
                ),
                region = region,
                latitude = form.cleaned_data['latitude'],
                longitude = form.cleaned_data['longitude'],
                location_description = form.cleaned_data['location_description']
            )
            
            # make sure they get one of those new passwords
            user.set_password(creation_args['password'])
            user.save()
            
            # Log them in and redirect to their profile page
            # HACK! http://groups.google.com/group/django-users/
            #    browse_thread/thread/39488db1864c595f
            user.backend='django.contrib.auth.backends.ModelBackend' 
            auth.login(request, user)
            return HttpResponseRedirect(person.get_absolute_url())
        else: print form.errors
    else:
        form = SignupForm()
    
    return render(request, 'signup.html', {
        'form': form,
        'api_key': settings.GOOGLE_MAPS_API_KEY,
    })

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
def upload_profile_photo(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Figure out what type of image it is
            image_content = request.FILES['photo']['content']
            format = Image.open(StringIO(image_content)).format
            format = format.lower().replace('jpeg', 'jpg')
            filename = md5.new(image_content).hexdigest() + '.' + format
            # Save the image
            path = os.path.join(settings.MEDIA_ROOT, 'profiles', filename)
            open(path, 'w').write(image_content)
            person.photo = 'profiles/%s' % filename
            person.save()
            return HttpResponseRedirect('/%s/upload/done/' % username)
    else:
        form = PhotoUploadForm()
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
    return render(request, 'country.html', {
        'country': country,
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
    person.profile_views += 1 # Not bothering with transactions; only a stat
    person.save()
   
    
    return render(request, 'profile.html', {
        'person': person,
        'api_key': settings.GOOGLE_MAPS_API_KEY,
        'is_owner': request.user.username == username,
    })

@must_be_owner
def edit_finding(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    if request.method == 'POST':
        form = FindingForm(request.POST, person=person)
        if form.is_valid():
            user = person.user
            user.email = form.cleaned_data['email']
            user.save()
            
            return HttpResponseRedirect('/%s/' % username)
    else:
        initial = {
            'email': person.user.email,
        }
        
        form = FindingForm(initial=initial, person=person)
    return render(request, 'edit_finding.html', {
        'form': form,
        'person': person,
    })

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
def edit_bio(request, username):
    person = get_object_or_404(KungfuPerson, user__username = username)
    if request.method == 'POST':
        form = BioForm(request.POST)
        if form.is_valid():
            person.bio = form.cleaned_data['bio']
            person.save()
            return HttpResponseRedirect('/%s/' % username)
    else:
        form = BioForm(initial = {'bio': person.bio})
    return render(request, 'edit_bio.html', {
        'form': form,
    })

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
            person.location_description = \
                form.cleaned_data['location_description']
            person.save()
            return HttpResponseRedirect('/%s/' % username)
    else:
        form = LocationForm()
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
        
    data = {}
    # XXX TODO
    #data = {'club_name': 'Fujian White Crane'}

    return render_json(data)