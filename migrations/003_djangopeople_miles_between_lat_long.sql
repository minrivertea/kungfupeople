CREATE LANGUAGE plpgsql;

CREATE OR REPLACE function miles_between_lat_long(  
  lat1 numeric, long1 numeric, lat2 numeric, long2 numeric  
) returns numeric  
language 'plpgsql' as $$  
declare  
  x numeric = 69.1 * (lat2 - lat1);  
  y numeric = 69.1 * (long2 - long1) * cos(lat1/57.3);  
begin  
  return sqrt(x * x + y * y);  
end  
$$;