## Various templatetags for misc stuff
##

from django.utils import simplejson
from django import template
from django.conf import settings

from sorl.thumbnail.main import DjangoThumbnail, get_thumbnail_setting
from sorl.thumbnail.processors import dynamic_import, get_valid_options
thumbnail_processors = dynamic_import(get_thumbnail_setting('PROCESSORS'))

try:
    from django_static import slimfile, staticfile
except ImportError:
    from django_static.templatetags.django_static import slimfile, staticfile
    

MAP_KEYS = settings.MAP_KEYS


register = template.Library()

def uniqify(seq, idfun=None):
    if seq is None:
        raise ValueError("Sequence can not be None")
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

@register.filter()
def country_flag_src(iso_code):
    return staticfile("/img/flags/%s.gif" % iso_code.lower())


## THIS MIGHT BE DEPRECATED BY NOW. AT LEAST IT SHOULD BE
@register.filter('nearby_people_escape')
def _nearby_people_escape(person):
    """return the person like this 
    
     {'latitude':<latitude>, 
      'longitude':<longitude>, 
      'fullname':<full name>, 
      #'username':<username>, 
      'location_description':<location_description>,
      'photo_thumbnail_url':<photo thumnail url>, 
      'country_iso_code': <country iso code lowercase>,
      'clubs':[{'name':<name>, 'url':<url within this site>}, ...], 
      'styles':[{'name':<name>, 'url':<url within this site>}, ...],
      }
    
    ...escaped for javascript.
    """
    data = dict(latitude=person.latitude, 
                longitude=person.longitude,
                fullname=unicode(person), 
                #username=person.user.username,
                user_url=person.get_absolute_url(),
                location_description=person.location_description,
                )
    
    if person.photo:
        thumbnail = DjangoThumbnail(person.photo, (60,60), opts=['crop'],
                                    processors=thumbnail_processors)
        data['photo_thumbnail_url'] = thumbnail.absolute_url
    else:
        data['photo_thumbnail_url'] = staticfile("/img/upload-a-photo-60.png")
        
    data['country_iso_code'] = person.country.iso_code.lower()
    data['clubs'] = []
    for club in person.club_membership.all():
        data['clubs'].append({'name': club.name, 'url':club.get_absolute_url()})
    
    _optimize_nearby_person_keys(data)
    return simplejson.dumps(data)

def _optimize_nearby_person_keys(data):
    """ if data is this:
    {'fullname': u'Peter', 'photo_thumbnail_url': '/img/foo.jpg'}
    then return this:
    {'C': u'Peter', 'E': '/img/foo.jpg'}
    """
    
    for k, v in data.items():
        if k in MAP_KEYS:
            data[MAP_KEYS[k]] = data.pop(k)

@register.filter("nearby_person_keys_js")
def _nearby_person_keys_js(key_definitions):
    js = "var MAP_KEYS=%s;\n" % simplejson.dumps(MAP_KEYS)
    #reversed = {}
    #for k, v in MAP_KEYS.items():
    #    reversed[v] = k
    #js += "var MAP_KEYS_REVERSED=%s;\n" % simplejson.dumps(reversed)
    return js

@register.filter("get_flag_image")
def _get_flag_image(country_iso_code):
    url = "/img/flags/%s.gif" % country_iso_code.lower()
    url = staticfile(url)
    return url