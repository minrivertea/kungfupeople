In this directory we put patches to the database in the form of SQL
migration scripts or other potential python migration scripts. 

I haven't really decided on a formal structure yet so I just create
.sql files with appropriate names. How do I generate these .sql files?

1. Add the new fields to your <appname>/models.py

2. Run ./manage sqldiff <appname> > 00x_<appname>_<fieldname>.sql

