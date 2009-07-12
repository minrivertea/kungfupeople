## Various templatetags for misc stuff
##

from django.utils import simplejson
from django import template

from sorl.thumbnail.main import DjangoThumbnail, get_thumbnail_setting
from sorl.thumbnail.processors import dynamic_import, get_valid_options
thumbnail_processors = dynamic_import(get_thumbnail_setting('PROCESSORS'))

try:
    from django_static import slimfile, staticfile
except ImportError:
    from django_static.templatetags.django_static import slimfile, staticfile

register = template.Library()

def uniqify(seq, idfun=None): 
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        ##if marker in seen: continue
        if seen.has_key(marker): continue
        seen[marker] = 1
        result.append(item)
    return result

@register.filter()
def uniqify_on(list_, on):
    return uniqify(list_, lambda x: getattr(x, on))


@register.filter('nearby_people_escape')
def _nearby_people_escape(person):
    """return the person like this 
    
     [<latitude>, <longitude>, <full name>, <username>, <location_description>, 
      <photo thumnail url>, <country iso code lowercase>]
    
    ...escaped for javascript.
    """
    data = [person.latitude, person.longitude,
            unicode(person), person.user.username,
            person.location_description,
            ]
    
    if person.photo:
        thumbnail = DjangoThumbnail(person.photo, (60,60), opts=[], 
                                    processors=thumbnail_processors)
        data.append(thumbnail.absolute_url)
    else:
        data.append(staticfile("/img/upload-a-photo-60.png"))
        
    data.append(person.country.iso_code.lower())
    return simplejson.dumps(data)
    

@register.filter("get_flag_image")
def _get_flag_image(country_iso_code):
    url = "/img/flags/%s.gif" % country_iso_code.lower()
    url = staticfile(url)
    return url