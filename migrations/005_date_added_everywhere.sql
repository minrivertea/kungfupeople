BEGIN;

ALTER TABLE djangopeople_club
  ADD date_added TIMESTAMP WITH TIME ZONE;
UPDATE djangopeople_club 
  SET date_added = add_date;
ALTER TABLE djangopeople_club
  DROP COLUMN add_date;


ALTER TABLE djangopeople_style
  ADD date_added TIMESTAMP WITH TIME ZONE;
UPDATE djangopeople_style 
  SET date_added = add_date;
ALTER TABLE djangopeople_style
  DROP COLUMN add_date;
  
ALTER TABLE djangopeople_video
  ADD date_added TIMESTAMP WITH TIME ZONE;
UPDATE djangopeople_video 
  SET date_added = add_date;
ALTER TABLE djangopeople_video
  DROP COLUMN add_date;  


ALTER TABLE djangopeople_autologinkey
  ADD date_added TIMESTAMP WITH TIME ZONE;
UPDATE djangopeople_autologinkey 
  SET date_added = add_date;
ALTER TABLE djangopeople_autologinkey
  DROP COLUMN add_date;  


ALTER TABLE djangopeople_recruitment
  ADD date_added TIMESTAMP WITH TIME ZONE;
UPDATE djangopeople_recruitment 
  SET date_added = add_date;
ALTER TABLE djangopeople_recruitment
  DROP COLUMN add_date;
  

ALTER TABLE newsletter_newsletter
  ADD date_added TIMESTAMP WITH TIME ZONE;
UPDATE newsletter_newsletter 
  SET date_added = add_date;
ALTER TABLE newsletter_newsletter
  DROP COLUMN add_date;


COMMIT;
