BEGIN;
-- Application: djangopeople
-- Model: Video
ALTER TABLE djangopeople_video
  ADD title VARCHAR(250);

ALTER TABLE djangopeople_video
  ALTER title SET DEFAULT '';

UPDATE djangopeople_video
  SET title = ''
  WHERE title IS NULL;

ALTER TABLE djangopeople_video
  ALTER title SET NOT NULL;
	
	
ALTER TABLE "djangopeople_video"
	ADD "youtube_video_id" varchar(100);
ALTER TABLE "djangopeople_video"
	ADD "thumbnail_url" varchar(250);
	
UPDATE 	djangopeople_video
SET title = description;

UPDATE 	djangopeople_video
SET description = '';

COMMIT;
