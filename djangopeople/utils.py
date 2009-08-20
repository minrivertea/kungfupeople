# python
import logging
import md5, datetime
from time import time

# django
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render_to_response
from django.template import RequestContext



ORIGIN_DATE = datetime.date(2000, 1, 1)


def render(request, template, context_dict=None, **kwargs):
    return render_to_response(
        template, context_dict or {}, context_instance=RequestContext(request),
                              **kwargs
    )

def render_basic(template, context_dict=None, **kwargs):
    return render_to_response(
        template, context_dict or {}, **kwargs
    )

def get_unique_user_cache_key(meta_request):
    bits = []
    bits.append(meta_request.get('HTTP_USER_AGENT',''))
    bits.append(meta_request.get('HTTP_ACCEPT_LANGUAGE',''))
    bits.append(meta_request.get('REMOTE_ADDR',''))
    return md5.new(''.join(bits)).hexdigest()


hex_to_int = lambda s: int(s, 16)
int_to_hex = lambda i: hex(i).replace('0x', '')

def lost_url_for_user(username):
    days = int_to_hex((datetime.date.today() - ORIGIN_DATE).days)
    hash = md5.new(settings.SECRET_KEY + days + username).hexdigest()
    return '/recover/%s/%s/%s/' % (
        username, days, hash
    )

def hash_is_valid(username, days, hash):
    if md5.new(settings.SECRET_KEY + days + username).hexdigest() != hash:
        return False # Hash failed
    # Ensure days is within a week of today
    days_now = (datetime.date.today() - ORIGIN_DATE).days
    days_old = days_now - hex_to_int(days)
    if days_old < 7:
        return True
    else:
        return False

def simple_decorator(decorator):
    """This decorator can be used to turn simple functions
    into well-behaved decorators, so long as the decorators
    are fairly simple. If a decorator expects a function and
    returns a function (no descriptors), and if it doesn't
    modify function attributes or docstring, then it is
    eligible to use this. Simply apply @simple_decorator to
    your decorator and it will automatically preserve the
    docstring and function attributes of functions to which
    it is applied."""
    # From http://wiki.python.org/moin/PythonDecoratorLibrary
    def new_decorator(f):
        g = decorator(f)
        g.__name__ = f.__name__
        g.__doc__ = f.__doc__
        g.__dict__.update(f.__dict__)
        return g
    # Now a few lines needed to make simple_decorator itself
    # be a well-behaved decorator.
    new_decorator.__name__ = decorator.__name__
    new_decorator.__doc__ = decorator.__doc__
    new_decorator.__dict__.update(decorator.__dict__)
    return new_decorator


import urllib2
def download_url(url, request_meta):

    headers = {}
    if request_meta.get('HTTP_USER_AGENT'):
        headers['User-Agent'] = request_meta.get('HTTP_USER_AGENT')
    if request_meta.get('HTTP_ACCEPT_LANGUAGE'):
        headers['Accept-Language'] = request_meta.get('HTTP_ACCEPT_LANGUAGE')
    if request_meta.get('HTTP_ACCEPT'):
        headers['Accept-Encoding'] = request_meta.get('HTTP_ACCEPT')
        
    req = urllib2.Request(url, None, headers)
    u = urllib2.urlopen(req)
    headers = u.info()
    return u.read()


from unaccent import unaccented_map
def unaccent_string(ustring, encoding="ascii"):
    if not isinstance(ustring, unicode):
        ustring = ustring.decode(encoding)
    return ustring.translate(unaccented_map()).encode(encoding, "ignore")


from django.http import HttpResponseForbidden

@simple_decorator
def must_be_owner(view):
    def inner(request, *args, **kwargs):
        if not request.user or request.user.is_anonymous() or request.user.username != args[0]:
            return HttpResponseForbidden('Not allowed')
        return view(request, *args, **kwargs)
    return inner


try:
    from prowlpy import Prowl
    if settings.PROWL_API_KEY:
        prowl_api = Prowl(settings.PROWL_API_KEY)
    else:
        prowl_api = None
except ImportError:
    import warnings
    warnings.warn("prowlpy no installed")
    prowl_api = None
        
def prowlpy_wrapper(event, description="",
                    application="KungfuPeople",
                    priority=None):
    if not prowl_api:
        return
    
    params = dict(application=application,
                  event=event,
                  description=description
                  )
    
    if priority is not None:
        # An integer value ranging [-2, 2]: Very Low, Moderate, Normal, High, Emergency
        priority = int(priority)
        assert priority >= -2 and priority <= 2
        params['priority'] = priority
    
    def params2cachekey(params):
        s = []
        for v in params.values():
            if isinstance(v, basestring):
                s.append(v.encode('utf8'))
            else:
                s.append(str(v))
        return ''.join(s)[:256]
    cache_key = params2cachekey(params)
    
    if not cache.get(cache_key):
    
        try:
            prowl_api.post(**params)
        except:
            logging.error("Error sending event %r" % event, exc_info=True)
            
        cache.set(cache_key, time(), 10)
                        
                        