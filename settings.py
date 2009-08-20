# Django settings for djangopeoplenet project.
import os
OUR_ROOT = os.path.realpath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Thumbnail settings
THUMBNAIL_DEBUG = True
THUMBNAIL_SUBDIR = '_thumbs'

# Tagging settings
FORCE_LOWERCASE_TAGS = True

AUTH_PROFILE_MODULE = 'djangopeople.KungfuPerson'
RECOVERY_EMAIL_FROM = 'chris@fry-it.com'

ADMINS = (
    ('Chris West', 'chris@fry-it.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'kungfupeople'             # Or path to database file if using sqlite3.
DATABASE_USER = 'root'             # Not used with sqlite3.
DATABASE_PASSWORD = 'gumball'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

GOOGLE_MAPS_API_KEY = open('localhost_googlemaps_api.key').read().strip()

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be avilable on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(OUR_ROOT, 'static')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'SECRET-KEY-GOES-HERE'

# Password used by the IRC bot for the API
API_PASSWORD = 'API-PASSWORD-GOES-HERE'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'context_processors.context',
)


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'djangopeople.middleware.RemoveWWW',
    'django.contrib.csrf.middleware.CsrfMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'djangopeople.middleware.NoDoubleSlashes',
    'djangopeople.middleware.AutoLogin',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    #'crashkit.CrashKitDjangoMiddleware',
)

ROOT_URLCONF = 'djangopeoplenet.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(OUR_ROOT, 'templates'),
    os.path.join(OUR_ROOT, 'djangopeople/templates'),
                 
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.flatpages',
    'djangopeople',
    'sorl.thumbnail',
    'django_static',
    'django.contrib.sitemaps',
    'newsletter',
                  
)


GOOGLE_ANALYTICS_TRACKER_ID = "" # set to something when you have set up an account

OFFLINE_MODE = False

# Putting these here will not suffice but for now, by putting it here it will work.
# It will work in context_processors.py for the templates but also accessible
# for the feeds.py
PROJECT_NAME = u"Kung Fu People"
PROJECT_MARTIAL_ART = u"Kung Fu"

# Who sends the newsletter?
NEWSLETTER_SENDER = "%s <noreply@kungfupeople.com>" % PROJECT_NAME
NEWSLETTER_HTML_TEMPLATE_BASE = "html_email_base.html"

PROWL_API_KEY = open('prowl-peterbe.key').read().strip()

CRASHKIT = None # enabled live

NEARBY_PERSON_KEYS = {'fullname':'A',
                      'latitude':'B',
                      'longitude':'C',
                      'username':'D',
                      'location_description':'E',
                      'country_iso_code':'F',
                      'photo_thumbnail_url':'G',
                      'user_url':'H',
                      'clubs':'I',
                      }


# default is 2 weeks, so we can safely increase that because there's nothing
# secure and confidential on this website
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7 * 2 * 10 # 20 weeks

try:
    from local_settings import *
except ImportError:
    pass
