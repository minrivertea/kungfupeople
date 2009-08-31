BEGIN;

ALTER TABLE djangopeople_club
  ADD clicks INT;

ALTER TABLE djangopeople_club
  ALTER clicks SET DEFAULT 0;

UPDATE djangopeople_club
  SET clicks = 0
  WHERE clicks IS NULL;

ALTER TABLE djangopeople_club
  ALTER clicks SET NOT NULL;


ALTER TABLE djangopeople_style
  ADD clicks INT;

ALTER TABLE djangopeople_style
  ALTER clicks SET DEFAULT 0;

UPDATE djangopeople_style
  SET clicks = 0
  WHERE clicks IS NULL;

ALTER TABLE djangopeople_style
  ALTER clicks SET NOT NULL;

COMMIT;
