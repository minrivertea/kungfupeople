# python
import datetime

# django
from django.template import RequestContext, Context
from django.template.loader import get_template
from django.template import Template
from django.db import models
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings

from djangopeople.models import AutoLoginKey


    
# settings.py
class InvalidVarException(object):
    def __mod__(self, missing):
        try:
            missing_str=unicode(missing)
        except:
            missing_str='Failed to create string representation'
        raise Exception('Unknown template variable %r %s' % (missing, missing_str))
    def __contains__(self, search):
        if search=='%s':
            return True
        return False

#TEMPLATE_DEBUG=True
#TEMPLATE_STRING_IF_INVALID = InvalidVarException()
    
    
def _get_context_for_all(last_send_date=None):
    context = {}
    
    # newsletter_issue_no is an integer number. It's basically a count
    # of which newsletter this is
    past_newsletters = Newsletter.objects.filter(send_date__lte=datetime.datetime.now())
    context['newsletter_issue_no'] = past_newsletters.count() + 1

    if Site._meta.installed:
        domain = Site.objects.get_current().domain
        def get_url(path):
            return 'http://%s%s' % (domain, path)
        context['site_url'] = get_url('/')

    return context
    

class Newsletter(models.Model):
    subject_template = models.CharField(max_length=100)
    text_template = models.TextField()
    
    send_date = models.DateTimeField(null=True, blank=True)
    
    add_date = models.DateTimeField('date added', default=datetime.datetime.now)
    modify_date = models.DateTimeField('date modified', auto_now=True)
    
    def __unicode__(self):
        return self.send_date.strftime('%A %b %Y')

    def _render_text(self, context):
        _before = settings.TEMPLATE_STRING_IF_INVALID
        settings.TEMPLATE_STRING_IF_INVALID = InvalidVarException()
        assert settings.TEMPLATE_DEBUG
        template = Template(self.text_template)
        rendered = template.render(context)
        settings.TEMPLATE_STRING_IF_INVALID = _before
        return rendered

    def _render_subject(self, context):
        _before = settings.TEMPLATE_STRING_IF_INVALID
        settings.TEMPLATE_STRING_IF_INVALID = InvalidVarException()
        assert settings.TEMPLATE_DEBUG
        template = Template(self.subject_template)
        rendered = template.render(context)
        settings.TEMPLATE_STRING_IF_INVALID = _before
        return rendered
    
    
    def _get_context_for_person(self, person, last_send_date=None):
        """return a dict of variables that can be used in the rendering 
        of the template.
        
        The optional parameter @last_send_date can be used to figure out 
        for example which Photos have been added since the last send date.
        """
        context = {}
        context['first_name'] = person.user.first_name
        context['last_name'] = person.user.last_name
        context['email'] = person.user.email
        context['username'] = person.user.username
        
        if Site._meta.installed:
            current_site = Site.objects.get_current()
            domain = current_site.domain
            def get_url(path):
                return 'http://%s%s' % (domain, path)
            context['profile_url'] = get_url(person.get_absolute_url())
        
        return context
    
    def _append_autologin_urls(self, person, context):
        """context is a dict like this:
          {'first_name': u'Peter', 
           'profile_url': 'http://example.com/peterbe',
           ...}
        
        Now, for every variable that ends with '_url' add
        '?alu=550269bc-bc67-4085-ba1a-04f3f0290288'
        (or &alu=... if ? is already in the URL)
        """
        alu = AutoLoginKey.get_or_create(person.user)
        for key in context.keys():
            if key.endswith('_url'):
                url = context[key]
            else:
                continue
            key += '_alu'
            if '?' in url:
                url += '&alu=%s' % alu.uuid
            else:
                url += '?alu=%s' % alu.uuid
            context[key] = url
        
    def send(self):
        from djangopeople.models import KungfuPerson
        
        people = KungfuPerson.objects.filter(user__is_active=True, 
                                             newsletter=True).select_related()
        extra_context = _get_context_for_all()
        for person in people:
            self._send_newsletter_to_person(person,
                                            extra_context=extra_context)
            
        self.send_date = datetime.datetime.now()
        self.save()
            
    def _send_newsletter_to_person(self, person, fail_silently=False,
                                   extra_context={}):
        # notice the order, this means that the context is overwritten by the 
        # person context if applicable
        extra_context.update(self._get_context_for_person(person))
        self._append_autologin_urls(person, extra_context)
        context = Context(extra_context)
        
        subject = self._render_subject(context)
        text = self._render_text(context)
        
        num_sent = send_mail(subject, text, settings.NEWSLETTER_SENDER,
                             [person.user.email],
                             fail_silently=fail_silently)
        
        # Assume that this method is called in non-transactional mode
        # so if the sending fails, we know to set sent=False
        
        sent = bool(num_sent)
        SentLog.objects.create(user=person.user,
                               subject=subject,
                               text=text,
                               send_date=datetime.datetime.now(),
                               sent=sent,
                               to=person.user.email)
        
        
        
        
                  
        
        
class SentLog(models.Model):
    user = models.ForeignKey(User)
    newsletter = models.ForeignKey(Newsletter, null=True) # for auditing
    subject = models.CharField(max_length=100)
    text = models.TextField()
    send_date = models.DateTimeField()
    # useful to log additionally in case the user changes her email address
    to = models.EmailField(null=True, blank=True)
    
    # A newsletter might have been generated for a user but not
    # successfully sent
    sent = models.BooleanField(default=True)

def _set_to_on_save(sender, instance, created, **__):
    if (created and not instance.to) or (not created and instance.to):
        user = instance.user
        instance.to = user.email
        
post_save.connect(_set_to_on_save, sender=SentLog)
        