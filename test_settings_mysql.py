# Same idea as test_settings.py but don't use sqlite
from settings import *

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = 'kungfupeople'
DATABASE_USER = 'root'
DATABASE_PASSWORD = 'test123'

CACHE_BACKEND = 'locmem:///'

PROWL_API_KEY = None
