BEGIN;
-- Application: djangopeople
-- Model: KungfuPerson
ALTER TABLE "djangopeople_kungfuperson"
ADD "came_from" varchar(250);
COMMIT;
