# python
import urllib

# django
from django.conf import settings
GOOGLE_MAPS_API_KEY = settings.GOOGLE_MAPS_API_KEY

def get_person_profile_static_map(person, size='1500x100', zoom=9):
    """return a static map that shows just one marker and is centred on this
    marker.
    """
    center = (person.latitude, person.longitude)
    marker = '%s,%s' % center
    
    return _get_static_map_url(marker, size, center, zoom)
                               
    
def _get_static_map_url(markers, size, center, zoom,
                        maptype=None, sensor='false'
                        ):
    assert isinstance(center, (tuple, list))
    assert len(center) == 2
    query_args = dict(markers=markers, size=size, 
                      key=GOOGLE_MAPS_API_KEY,
                      sensor=sensor,
                      center='%s,%s' % center,
                      zoom=zoom,
                     )
    if maptype:
        assert maptype in ('roadmap', 'satellite', 'hybrid', 'terrain')
        query_args['maptype'] = maptype
        
    google_maps_url = 'http://maps.google.com/staticmap?' + urllib.urlencode(query_args)
    
    # we should now download this map and put a reference to it
    # TODO
    
    return google_maps_url 
    