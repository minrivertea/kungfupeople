# Same idea as test_settings.py but don't use sqlite
from settings import *

#DATABASE_ENGINE = 'sqlite3'
#DATABASE_NAME = TEST_DATABASE_NAME = ':memory:'

CACHE_BACKEND = 'locmem:///'

PROWL_API_KEY = None
