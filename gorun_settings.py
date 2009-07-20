DIRECTORIES = (
   ('newsletter/unit_tests/test_views.py',
    './manage.py test --settings=test_settings newsletter.ViewsTestCase'),
    
   ('newsletter/unit_tests', 
    './manage.py test --settings=test_settings newsletter'),

   ('newsletter/views.py',
    './manage.py test --settings=test_settings newsletter.ViewsTestCase.test_find_clubs_by_location'),


   ('djangopeople/unit_tests/test_views.py',
    './manage.py test --settings=test_settings djangopeople.ViewsTestCase.test_find_clubs_by_location'),
               
   ('djangopeople/models.py',
    './manage.py test --settings=test_settings djangopeople.ViewsTestCase.test_find_clubs_by_location'),
   ('djangopeople/views.py',
    './manage.py test --settings=test_settings djangopeople.ViewsTestCase'),

   ('/home/peterbe/dev/DJANGO/django-static/django_static/templatetags/django_static.py',
    './manage.py test --settings=test_settings django_static.TestDjangoStatic'),

   ('/home/peterbe/dev/DJANGO/django-static/django_static/tests.py',
    './manage.py test --settings=test_settings django_static.TestDjangoStatic'),
    
#   ('djangopeople/views.py', './run_djangopeople_fcgi.sh'),

)

