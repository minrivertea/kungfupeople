from django.conf import settings

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
        data['show_notice'] = {'url': '/new-features/',
                               'text': 'check out the latest features here!',
                               'leadin': 'Hey %s' % request.user.first_name,
                              }
    else:
        current_url = request.build_absolute_uri()
        if '/signup' not in current_url:
            data['show_signup_notice'] = True
    

    return data

