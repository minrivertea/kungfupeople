BEGIN;

alter TABLE djangopeople_kungfuperson ALTER location_description type varchar(100);

COMMIT;
