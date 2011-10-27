# Django settings for djangopeoplenet project.
import os
OUR_ROOT = os.path.realpath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Thumbnail settings
THUMBNAIL_DEBUG = False # not sure what this means!
THUMBNAIL_SUBDIR = '_thumbs'

# Tagging settings
FORCE_LOWERCASE_TAGS = True

AUTH_PROFILE_MODULE = 'djangopeople.KungfuPerson'
RECOVERY_EMAIL_FROM = 'chris@fry-it.com'
NOREPLY_EMAIL = 'noreply@kungfupeople.com'

ADMINS = (
    ('Chris West', 'chris@fry-it.com'),
    ('Peter Bengtsson', 'peter@fry-it.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = ''           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

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
SECRET_KEY = ''

# Password used by the IRC bot for the API
API_PASSWORD = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
#    'ab.loaders.load_template_source',
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'djangopeople.context_processors.context',
)


MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'djangopeople.middleware.RemoveWWW',
    'djangopeople.middleware.SWFUploadFileMiddleware',
    'django.middleware.csrf.CsrfMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'djangopeople.middleware.NoDoubleSlashes',
    'djangopeople.middleware.AutoLogin',
    'djangopeople.middleware.Recruitment',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'hoptoad.middleware.HoptoadNotifierMiddleware',
#    'ab.middleware.ABMiddleware',

)

ROOT_URLCONF = 'djangopeoplenet.urls'

LOGIN_URL = '/login/'
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(OUR_ROOT, 'templates'),
#    os.path.join(OUR_ROOT, 'djangopeople/templates'),

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
    'stats',
    'welcome',
#    'ab',
    'twitter',
)

MIGRATIONS_ROOT = os.path.join(OUR_ROOT, 'migrations')

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

OFFLINE_MODE = False

# Putting these here will not suffice but for now, by putting it here it will work.
# It will work in context_processors.py for the templates but also accessible
# for the feeds.py
PROJECT_NAME = u"Kung Fu People"
PROJECT_MARTIAL_ART = u"Kung Fu"

# Who sends the newsletter?
NEWSLETTER_SENDER = "%s <noreply@kungfupeople.com>" % PROJECT_NAME
NEWSLETTER_HTML_TEMPLATE_BASE = "html_email_base.html"

# Who sends the welcome email
WELCOME_EMAIL_SENDER = NEWSLETTER_SENDER

CRASHKIT = None # enabled live

MAP_KEYS = {'fullname':'A',
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
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
# NOTE! SESSION_COOKIE_AGE can not be more than 30 days otherwise
# the django.contrib.sessions.backends.cached_db won't use memcache to store the
# sessions. Thanks for the tip Bruno!

#SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'


# Anonymous view renderings are cached for an hour
USE_CACHE_PAGE = True

try:
    from local_settings import *
except ImportError:
    pass
