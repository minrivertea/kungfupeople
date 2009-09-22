from django.db import models
from django.contrib.auth.models import User

import oauth

class TwitterUser(models.Model):
    
    user = models.ForeignKey(User)
    token = models.CharField(max_length=2048)

    #objects = UserManager()

    def __unicode__(self):
        return u'%s (%s...)' % (self.user.username, self.token[:40])

    def get_oauth_token(self):
        """Returns a OAuthToken object"""
        return oauth.OAuthToken.from_string(self.token)

