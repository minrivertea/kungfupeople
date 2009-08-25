To populate a bunch of fake users run:

$ ./manage.py populate_random_people [10]

You can delete them later since they all have usernames that end in
'random'.


To run the unit tests::

 $ ./manage.py test --settings=test_settings newsletter djangopeople
 
 
