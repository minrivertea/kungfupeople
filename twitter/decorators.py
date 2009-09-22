from django.utils import simplejson

from video.models import TwitterUser
from utils import is_authenticated
from utils import CONSUMER, CONNECTION

import oauth

def twitter_auth(function):
    def check_auth(request, *args, **kwargs):
        if request.session.has_key('access_token'):
            access_token = request.session.get('access_token')
            try:
                request.user = TwitterUser.objects.get(token=access_token)
            except TwitterUser.DoesNotExist:
                # Let's create a user
                token = oauth.OAuthToken.from_string(access_token)
                auth = is_authenticated(token)
                if auth:
                    creds = simplejson.loads(auth)
                    name = creds.get('screen_name') # Twitter username
                    user = TwitterUser.objects.create_user(username=name, token=access_token)
                    user.save()
                    request.user = user
                else: # Warning / whatever
                    pass
        else:
            request.user = None
        return function(request, *args, **kwargs)
    return check_auth

