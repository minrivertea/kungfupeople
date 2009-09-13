# python
import datetime

# django
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.sites.models import RequestSite

# other
from premailer import Premailer

# project
from djangopeople.utils import render
from djangopeople.models import Photo, Club, Style, DiaryEntry, Video, \
  AutoLoginKey
from models import WelcomeEmail

def create_welcome_email(user, request):
    # fish out all the relevant information about the user and
    # then create an unsent WelcomeEmail
    
    subject = "Welcome to %s" % settings.PROJECT_NAME
    person = user.get_profile()
    
    alu = AutoLoginKey.get_or_create(user)
    profile_url = reverse('person.view', args=(user.username,))
    upload_photo_url = reverse('upload_photo', args=(user.username,))
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
            
    #profile_url_alu = alu_url(profile_url)
    #upload_photo_url_alu = alu_url(upload_photo_url)
    
    # now the interesting thing starts. We need to find out what they haven't
    # done with their profile and pester them about that.
    response = render(request, 'welcome-email.html', data)
    html = response.content
    
    
    html = Premailer(html, base_url=base_url,
                     keep_style_tags=False,
                    ).transform()
    print html
    
    return WelcomeEmail.objects.create(user=user,
                                       subject=subject,
                                       body=html,
                                      )

def create_welcome_emails(request):
    """figure out what people to send welcome emails to and then send them.
    The people to consider for this is those who haven't received an email 
    and are younger than a day.
    """
    
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    day_before_yesterday = yesterday-datetime.timedelta(days=1)
    users = User.objects.filter(date_joined__gte=day_before_yesterday)
    users = users.filter(date_joined__lte=yesterday)
    users = [user for user in users 
             if not WelcomeEmail.objects.filter(user=user).count()]
    
    count = 0
    for user in users:
        welcome_email = create_welcome_email(user, request)
        count += 1
        
    if count:
        if count == 1:
            msg = 'Created 1 welcome email'
        else:
            msg = 'Created %s welcome emails' % count
    else:
        msg = 'No welcome emails this time'
    return HttpResponse(msg)
                
        
    
    
