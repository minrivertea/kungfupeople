BEGIN;
-- Application: djangopeople
-- Model: KungfuPerson
ALTER TABLE "djangopeople_kungfuperson"
	ADD "newsletter" varchar(5);
COMMIT;
