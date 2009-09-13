# python
import datetime

# django
from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.conf import settings

# project
from djangopeople.html2plaintext import html2plaintext
from newsletter.multipart_email import send_multipart_mail

class WelcomeEmail(models.Model):
    user = models.ForeignKey(User, unique=True)
    email = models.EmailField(null=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    
    send_date = models.DateTimeField(null=True, blank=True)
    
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs and 'email' not in kwargs:
            kwargs['email'] = kwargs['user'].email
        super(WelcomeEmail, self).__init__(*args, **kwargs)
        
    def __unicode__(self):
        return u"'%s' to %s (%s)" % \
          (self.subject, self.user.get_full_name(), self.user.email)
    
    def send(self):
        """return true if if was successfully sent"""
        assert self.subject, "no subject"
        assert self.body, "no body"
        sent = self._send_email()
        self.send_date = datetime.datetime.now()
        self.save()
        return sent
        
    def _send_email(self):
        # bits here stolen from the newsletter app
        html = self.body
        text = html2plaintext(html, encoding='utf-8')
        
        email = self.email and self.email or self.user.email
        num_sent = send_multipart_mail(text, html, 
                                       self.subject,
                                       [email],
                                       fail_silently=False,
                                       sender=settings.WELCOME_EMAIL_SENDER,
                                       bcc=[x[1] for x in settings.ADMINS],
                                      )
        return bool(num_sent)
    
    @classmethod
    def get_users_to_welcome(cls):
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        day_before_yesterday = yesterday-datetime.timedelta(days=1)
        users = User.objects.filter(date_joined__gte=day_before_yesterday)
        users = users.filter(date_joined__lte=yesterday)
        return [user for user in users 
                if not cls.objects.filter(user=user).count()]
    