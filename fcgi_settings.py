from settings import *


DEBUG = False
TEMPLATE_DEBUG = DEBUG

GOOGLE_ANALYTICS_TRACKER_ID = None
OFFLINE_MODE = False

DJANGO_STATIC = True
DJANGO_STATIC_NAME_PREFIX = '/cache-forever'
DJANGO_STATIC_SAVE_PREFIX = '/tmp/django-static-forever/cache-forever'

GOOGLE_MAPS_API_KEY = open('kungfupeople.local_googlemaps_api.key').read().strip()

ADMINS = (
    ('Peter Bengtsson', 'peter@fry-it.com'),
)

EMAIL_HOST = 'localhost'
EMAIL_SUBJECT_PREFIX = '[KFP] '
SERVER_EMAIL = 'django@kungfupeople.local'

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages' # change this to a proper location
