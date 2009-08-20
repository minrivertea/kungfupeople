from settings import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

GOOGLE_ANALYTICS_TRACKER_ID = None
OFFLINE_MODE = False

DJANGO_STATIC = True
DJANGO_STATIC_NAME_PREFIX = '/cache-forever'
DJANGO_STATIC_SAVE_PREFIX = '/tmp/django-static-forever/cache-forever'

GOOGLE_MAPS_API_KEY = open('kungfupeople.local_googlemaps_api.key').read().strip()