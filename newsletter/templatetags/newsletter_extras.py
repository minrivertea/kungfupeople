## Various templatetags for misc stuff
##

from urlparse import urlparse, urlunparse
#from django.utils import simplejson
from django import template
#from django.conf import settings

#from sorl.thumbnail.main import DjangoThumbnail, get_thumbnail_setting
#from sorl.thumbnail.processors import dynamic_import, get_valid_options
#thumbnail_processors = dynamic_import(get_thumbnail_setting('PROCESSORS'))

#try:
#    from django_static import slimfile, staticfile
#except ImportError:
#    from django_static.templatetags.django_static import slimfile, staticfile
    
register = template.Library()

@register.filter()
def add2url(url, addition):
    """ a URL might look like this:
    'http://www.com/path/?cgi=abc#top' and to this we want to add
    'subdirectory/'
    Then we simply can't do url + addition
    """
    url_parts = urlparse(url)
    add_parts = urlparse(addition)
    combined = list(url_parts)[:]
    combined[2] = url_parts[2] + add_parts[2]
    if url_parts[4] and add_parts[4]:
        combined[4] = '%s&%s' % (url_parts[4], add_parts[4])
    elif add_parts[4]:
        combined[4] = add_parts[4]
    if add_parts[-1]:
        combined[-1] = add_parts[-1] # overwrite
    return urlunparse(combined)
    