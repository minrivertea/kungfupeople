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
from django.db.models.signals import post_save, pre_save
from django.conf import settings

from djangopeople.models import AutoLoginKey
from djangopeople.html2plaintext import html2plaintext

from newsletter.premailer import Premailer

    
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


class NewsletterTemplateError(Exception):
    pass


class Newsletter(models.Model):
    subject_template = models.CharField(max_length=100)
    
    # articially, you can't have a Newsletter with either text_template
    # nor html_text_template but allowing null on either solves the 
    # intermediate problem
    text_template = models.TextField(null=True, blank=True)
    html_text_template = models.TextField(null=True, blank=True)
    
    send_date = models.DateTimeField(null=True, blank=True)
    
    add_date = models.DateTimeField('date added', default=datetime.datetime.now)
    modify_date = models.DateTimeField('date modified', auto_now=True)
    
    def __unicode__(self):
        return self.send_date.strftime('%A %b %Y')

    def _render_text(self, context):
        return self._render_template(context, self.text_template)

    def _render_html_text(self, context):
        return self._render_template(context, self.html_text_template)

    def _render_subject(self, context):
        return self._render_template(context, self.subject_template)
    
    def _wrap_html_template(self, body_content, template_path):
        template = get_template(template_path)
        context = Context(dict(body_content=body_content))
        return template.render(context)
        #return self._render_template(context, template)
    
    def _render_template(self, context, template_as_string):
        _before = settings.TEMPLATE_STRING_IF_INVALID
        settings.TEMPLATE_STRING_IF_INVALID = InvalidVarException()
        assert settings.TEMPLATE_DEBUG
        template = Template(template_as_string)
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
        
    def send(self, max_sendouts=100):
        if not self.text_template and not self.html_text_template:
            raise NewsletterTemplateError(
              "Must have text_template or html_text_template")
        
        from djangopeople.models import KungfuPerson

        people = KungfuPerson.objects.\
          filter(user__is_active=True, newsletter=True)
        
        # possible recipients due to the 'max_sendouts'. Therefore, it's quite
        # possible that that a newsletter has been sent to 10 out of 100 
        # possible people and it's not until it's been sent to all 100 that this
        # newsletter gets the 'send_date' set to todays date.
        # Exclude the people who've already been emailed.
        sent_to_user_ids = [x.user.id for x 
                            in SentLog.objects.filter(newsletter=self)]
        if sent_to_user_ids:
            people = people.exclude(user__id__in=sent_to_user_ids)
        
        possible_sendouts = people.count()
        
        extra_context = _get_context_for_all()
        for person in people.select_related()[:max_sendouts]:
            self._send_newsletter_to_person(person,
                                            extra_context=extra_context)
            
        if max_sendouts > possible_sendouts:
            self.send_date = datetime.datetime.now()
            self.save()
        #else:
        #    print "needs to send more later"
            
    def _send_newsletter_to_person(self, person, fail_silently=False,
                                   extra_context={}):
        # notice the order, this means that the context is overwritten by the 
        # person context if applicable
        extra_context.update(self._get_context_for_person(person))
        self._append_autologin_urls(person, extra_context)
        context = Context(extra_context)
        
        subject = self._render_subject(context)
        html = None
        if self.text_template and self.html_text_template:
            text = self._render_text(context)
            html = self._render_html_text(context)
        elif self.text_template:
            text = self._render_text(context)
            html = None
        else:
            html = self._render_html_text(context)
            text = html2plaintext(html, encoding='utf-8')
            
        if html:
            # now wrap this in the header and footer
            html = self._wrap_html_template(html,
                                     settings.NEWSLETTER_HTML_TEMPLATE_BASE)
            
            html = Premailer(html).transform()
            
            ## XXX: Consider looking into http://www.campaignmonitor.com/testing/
            ## and what it can offer us
            
            from multipart_email import send_multipart_mail
            num_sent = send_multipart_mail(text, html, subject,
                                           [person.user.email],
                                           fail_silently=fail_silently,
                                           sender=settings.NEWSLETTER_SENDER
                                           )

        else:
            num_sent = send_mail(subject, text, settings.NEWSLETTER_SENDER,
                                [person.user.email],
                                fail_silently=fail_silently)
            
        # Assume that this method is called in non-transactional mode
        # so if the sending fails, we know to set sent=False
        
        sent = bool(num_sent)
        SentLog.objects.create(newsletter=self,
                               user=person.user,
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
