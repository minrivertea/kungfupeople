# python
import datetime

# django
from django.conf import settings

# other
from sorl.thumbnail.main import DjangoThumbnail, get_thumbnail_setting
from sorl.thumbnail.processors import dynamic_import, get_valid_options
thumbnail_processors = dynamic_import(get_thumbnail_setting('PROCESSORS'))

# app
from models import KungfuPerson, Photo, DiaryEntry


def context(request):

    data = {'TEMPLATE_DEBUG': settings.TEMPLATE_DEBUG,
            'DEBUG': settings.DEBUG,
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
            'OFFLINE_MODE': settings.OFFLINE_MODE,
            'base_template': "base.html",
            'mobile_version': False,
            'mobile_user_agent': False,
            'PROJECT_NAME': settings.PROJECT_NAME,
            'PROJECT_MARTIAL_ART': settings.PROJECT_MARTIAL_ART,
            }
    
    data['show_signup_notice'] = False
    if request.user.is_authenticated():
        since = request.session.get('noticed_recent_stuff', None)
        if since is None:
            # By defauly check for recent activity in the last hour
            since = datetime.datetime.now() - datetime.timedelta(hours=1)
            request.session['noticed_recent_stuff'] = since
            _has_since = False
        else:
            _has_since = True
        
        # check if someone has signed up recently
        for person in KungfuPerson.objects.\
          filter(user__date_joined__gte=since).\
            exclude(user__id=request.user.id).\
              order_by('-user__date_joined').select_related():
            
            text = "%s %s from %s just joined!" % \
              (person.user.first_name,
               person.user.last_name,
               person.country.name)
            
            #if person.photo:
            #    thumbnail = DjangoThumbnail(person.photo, (40,40),
            #                                opts=[], 
            #                                processors=thumbnail_processors, 
            #                                **{})
            #    thumbnail_url = thumbnail.absolute_url
            #    text = ('<img src="%s" alt="%s" border="0"/> ' %\
            #             (thumbnail_url, text)) + text
            
            data['show_notice'] = {'url': person.get_absolute_url(),
                                   'leadin': "Great!",
                                   'text': text,
                                   }
            request.session['noticed_recent_stuff'] = \
              person.user.date_joined + datetime.timedelta(minutes=1)
            break
        else:
            # no new signups recently, has a photo been added recently?
            for photo in Photo.objects.\
              filter(date_added__gte=since).\
                exclude(user__id=request.user.id).\
                  select_related():
                text = u"%s %s uploaded a photo" % \
                  (photo.user.first_name, photo.user.last_name)
                
                #thumbnail = DjangoThumbnail(photo.photo, (40,40),
                #                            opts=[], 
                #                            processors=thumbnail_processors, 
                #                            **{})
                #thumbnail_url = thumbnail.absolute_url
                #text = ('<img src="%s" alt="%s" border="0" class="thumbnail-in-notice"/> ' %\
                #         (thumbnail_url, text)) + text
                
                data['show_notice'] = {'url': photo.get_absolute_url(),
                                       'leadin': "Snap!",
                                       'text': text,
                                      }
                request.session['noticed_recent_stuff'] = \
                  photo.date_added + datetime.timedelta(minutes=1)
                
                break
                                      
        if not _has_since and 'show_notice' not in data:
            data['show_notice'] = {'url': '/new-features/',
                                   'text': 'check out the latest features here!',
                                   'leadin': 'Hey %s' % request.user.first_name,
                                  }
    else:
        current_url = request.build_absolute_uri()
        if '/signup' not in current_url:
            data['show_signup_notice'] = True
    
    print "noticed_recent_stuff", repr(request.session.get('noticed_recent_stuff'))
    return data

