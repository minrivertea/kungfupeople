# python
import datetime

# django
from django.conf import settings

# other
from sorl.thumbnail.main import DjangoThumbnail, get_thumbnail_setting
from sorl.thumbnail.processors import dynamic_import, get_valid_options
thumbnail_processors = dynamic_import(get_thumbnail_setting('PROCESSORS'))

# app
from djangopeople.models import KungfuPerson, Photo, DiaryEntry

THIS_YEAR = datetime.datetime.today().strftime('%Y')

def context(request):

    data = {'TEMPLATE_DEBUG': settings.TEMPLATE_DEBUG,
            'DEBUG': settings.DEBUG,
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
            'GOOGLE_ANALYTICS_TRACKER_ID': settings.GOOGLE_ANALYTICS_TRACKER_ID,
            'OFFLINE_MODE': settings.OFFLINE_MODE,
            'base_template': "base.html",
            'mobile_version': False,
            'mobile_user_agent': False,
            'PROJECT_NAME': settings.PROJECT_NAME,
            'PROJECT_MARTIAL_ART': settings.PROJECT_MARTIAL_ART,
            'COPYRIGHT_YEAR': THIS_YEAR,
            
            }
    
    data['MAP_KEYS'] = settings.MAP_KEYS
    
    return data

