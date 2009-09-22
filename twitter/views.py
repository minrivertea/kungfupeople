# django
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import simplejson
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from djangopeople.models import KungfuPerson
from models import TwitterUser
from djangopeople.views import signup
import oauth
from twitter.utils import CONSUMER, CONNECTION
from twitter.utils import get_unauthorised_request_token, get_authorisation_url, \
        exchange_request_token_for_access_token, is_authenticated


def auth(request):
    """Sends the user to twitter's auth page"""
    token = get_unauthorised_request_token(CONSUMER, CONNECTION)
    auth_url = get_authorisation_url(CONSUMER, token)
    response = HttpResponseRedirect(auth_url)
    request.session['unauthed_token'] = token.to_string()
    return response

def unauth(request):
    """Log out from the website"""
    request.session.clear()
    return HttpResponseRedirect('/')

def return_(request):
    """Twitter OAuth return URL"""
    unauthed_token = request.session.get('unauthed_token', None)
    if not unauthed_token:
        return HttpResponse("No un-authed token cookie")
    token = oauth.OAuthToken.from_string(unauthed_token)
    if token.key != request.GET.get('oauth_token', 'no-token'):
        return HttpResponse("Something went wrong! Tokens do not match")
    access_token = exchange_request_token_for_access_token(CONSUMER, CONNECTION, token)
    request.session['access_token'] = access_token.to_string()
    # if the twitter user already exists and has a complete profile
    # redirect them to their profile page
    try:
        user = TwitterUser.objects.get(token=access_token.to_string()).user
        try:
            person = user.get_profile()
            # log in as this user
            from django.contrib.auth import load_backend, login
            for backend in settings.AUTHENTICATION_BACKENDS:
                if user == load_backend(backend).get_user(user.pk):
                    user.backend = backend
            if hasattr(user, 'backend'):
                login(request, user)
            return HttpResponseRedirect(person.get_absolute_url())
        except KungfuPerson.DoesNotExist:
            pass
    except TwitterUser.DoesNotExist:
        pass
    return HttpResponseRedirect(reverse('twitter_signup'))

def _random_password(prefix=''):
    from random import random
    return prefix + str(random()*10000)

def twitter_signup(request):
    if not request.session.get('access_token'):
        return HttpResponseRedirect(reverse('auth'))
    access_token = request.session.get('access_token')
    try:
        user = TwitterUser.objects.get(token=access_token).user
        # DECIDE IF THE PROFILE IS COMPLETE
        try:
            person = user.get_profile()
        except KungfuPerson.DoesNotExist:
            # proceed and sign up a full profile
            return signup(request, initial_user=user)
        
        # XXX: At this point we could potentially redirect the user to say
        # to the user: _Your profile_ already exists. Do you want to create
        # a new account?

        # log in as this user
        from django.contrib.auth import load_backend, login
        for backend in settings.AUTHENTICATION_BACKENDS:
            if user == load_backend(backend).get_user(user.pk):
                user.backend = backend
        if hasattr(user, 'backend'):
            login(request, user)
        print "twitter user exists"
        return HttpResponseRedirect('/') # came_from?
        
    except TwitterUser.DoesNotExist:
        # create a new user
        token = oauth.OAuthToken.from_string(access_token)
        auth = is_authenticated(token)
        if auth:
            
            creds = simplejson.loads(auth)
            from pprint import pprint
            pprint(creds)
            username = base_username = creds.get('screen_name') # Twitter username
            email = creds.get('email', 'twitteruser@kungfupeople.com')
            count = 2
            while User.objects.filter(username__iexact=username).count():
                username = '%s%s' % (base_username, count)
                count += 1
            user = User.objects.create_user(username, email,
                                            _random_password(prefix='twitteruser'),
                                           )
            TwitterUser.objects.create(user=user, token=access_token)
            return signup(request, initial_user=user)
            
    return HttpResponse(request.session.get('access_token'))

def reset_session(request):
    keys_before = request.session.keys()
    request.session.clear()
    return HttpResponse('Reset - removed: %s' % ', '.join(keys_before))