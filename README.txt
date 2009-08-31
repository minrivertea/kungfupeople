To populate a bunch of fake users run:

$ ./manage.py populate_random_people [10]

You can delete them later since they all have usernames that end in
'random'.


To run the unit tests::

 $ ./manage.py test --settings=test_settings newsletter djangopeople
 
If you're going to run a lot of unit tests you might want to NOT test
the YouTube API every single time. To NOT test YouTube, set an
environement variable called DONT_TEST_YOUTUBE::

 $ export DONT_TEST_YOUTUBE=1