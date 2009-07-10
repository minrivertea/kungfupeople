BEGIN;
-- Application: djangopeople
-- Model: AutoLoginKey
CREATE INDEX "djangopeople_autologinkey_uuid_idx"
	ON "djangopeople_autologinkey" ("uuid");
-- Model: KungfuPerson
ALTER TABLE "djangopeople_kungfuperson"
	ADD "newsletter" boolean;
COMMIT;
