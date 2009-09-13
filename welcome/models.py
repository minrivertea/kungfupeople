# python
import datetime

# django
from django.db import models
from django.contrib.auth.models import User
from django.shortcuts import render_to_response

# project


class WelcomeEmail(models.Model):
    user = models.ForeignKey(User, unique=True)
    email = models.EmailField(null=True)
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    
    send_date = models.DateTimeField(null=True, blank=True)
    
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs and 'email' not in kwargs:
            kwargs['email'] = kwargs['user'].email
        super(WelcomeEmail, self).__init__(*args, **kwargs)
    
    def send(self):
        self._send_email()
        self.send_date = datetime.datetime.now()
        self.save()
        
    def _send_email(self):
        # stub
        pass 
    
    
        
