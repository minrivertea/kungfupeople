# python
import datetime

# django
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.sites.models import RequestSite
from django.db import transaction

# other
from premailer import Premailer

# project
from djangopeople.utils import render
from djangopeople.models import Photo, Club, Style, DiaryEntry, Video, \
  AutoLoginKey, KungfuPerson
from models import WelcomeEmail

def create_welcome_email(user, request):
    # fish out all the relevant information about the user and
    # then create an unsent WelcomeEmail
    
    subject = u"Welcome to %s" % settings.PROJECT_NAME
    try:
        person = user.get_profile()
    except KungfuPerson.DoesNotExist:
        return None
    
    alu = AutoLoginKey.get_or_create(user)
    profile_url = reverse('person.view', args=(user.username,))
    upload_photo_url = reverse('upload_profile_photo', args=(user.username,))
    change_password_url = reverse("edit_password", args=(user.username,))
    edit_style_url = reverse("edit_style", args=(user.username,))
    edit_club_url = reverse("edit_club", args=(user.username,))
    edit_profile_url = reverse("edit_profile", args=(user.username,))
    
    data = locals()
    
    domain = RequestSite(request).domain
    base_url = 'http://%s' % domain
    
    # for every variable that ends with _url make it an absolute url
    # and add the _alu variable
    def aluify_url(url):
        if '?' in url:
            return url + '&alu=%s' % alu.uuid
        else:
            return url + '?alu=%s' % alu.uuid
        
    keys = list(data.keys())
    for key in keys:
        if key.endswith('_url'):
            url = data[key]
            if url.startswith('/'):
                url = base_url + url
            data[key] = url
            data[key + '_alu'] = aluify_url(url)
            
    # now the interesting thing starts. We need to find out what they haven't
    # done with their profile and pester them about that.
    response = render(request, 'welcome-email.html', data)
    html = response.content
    
    
    html = Premailer(html, base_url=base_url,
                     keep_style_tags=False,
                    ).transform()
    
    return WelcomeEmail.objects.create(user=user,
                                       subject=subject,
                                       body=html,
                                      )

    
@transaction.commit_on_success
def create_welcome_emails(request):
    """figure out what people to send welcome emails to and then send them.
    The people to consider for this is those who haven't received an email 
    and are younger than a day.
    """
    
    users = WelcomeEmail.get_users_to_welcome()
    
    count = 0
    for user in users:
        welcome_email = create_welcome_email(user, request)
        if welcome_email is not None:
            count += 1
        
    if count:
        if count == 1:
            msg = 'Created 1 welcome email'
        else:
            msg = 'Created %s welcome emails' % count
    else:
        msg = 'No welcome emails this time'
    return HttpResponse(msg)
                
        
def send_unsent_emails(request):
    count = count_success = 0
    for welcome_email in WelcomeEmail.objects.filter(send_date__isnull=True):
        if welcome_email.send():
            count_success += 1
        count += 1

    if not count:
        return HttpResponse('No emails sent')
    
    if count == count_success:
        if count == 1:
            return HttpResponse('Sent 1 email')
        else:
            return HttpResponse('Sent %s emails' % count)
    else:
        return HttpResponse('%s emails attempted, %s failed :(' % \
                            (count, count - count_success))
        
        
    
def create_and_send_emails(request):
    """lazy one you can use for cron jobs"""
    count_before = WelcomeEmail.objects.filter(send_date__isnull=True).count()
    result = create_welcome_emails(request)
    count_after = WelcomeEmail.objects.filter(send_date__isnull=True).count()
    if count_after == count_before:
        return result
    else:
        return send_unsent_emails(request)
    