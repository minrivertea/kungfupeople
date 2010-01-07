BEGIN;
-- Application: djangopeople
-- Model: Club
ALTER TABLE "djangopeople_club"
	ALTER "slug" TYPE varchar(200);
-- Model: DiaryEntry
ALTER TABLE "djangopeople_diaryentry"
	ALTER "location_description" TYPE varchar(100);
-- Model: KungfuPerson
ALTER TABLE "djangopeople_kungfuperson"
	ALTER "location_description" TYPE varchar(50);
COMMIT;
