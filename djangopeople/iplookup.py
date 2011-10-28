import urllib
import urllib2
import logging
import xml.etree.ElementTree as etree
from cStringIO import StringIO

def getGeolocationByIP(ip):
    query_args = {'ip':ip}
    encoded_args = urllib.urlencode(query_args)

    url = 'http://ipinfodb.com/ip_query.php?' + encoded_args
    try:
        content = urllib2.urlopen(url).read()
    except urllib2.URLError, msg:
        raise urllib2.URLError(str(msg) + " URL trying to open: %s" % url)

    t = etree.ElementTree().parse(StringIO(content))
    return {'country': t.find("CountryName").text or '',
            'country_code': t.find("CountryCode").text or '',
            'city': t.find("City").text or '',
            'region': t.find("RegionName").text or '',
            'lat': float(t.find("Latitude").text),
            'lng': float(t.find("Longitude").text)
           }

from django.core.cache import cache
def getGeolocationByIP_cached(ip):
    cache_key = "iplookup_%s" % ip
    result = cache.get(cache_key)
    if result is None:
        try:
            result = getGeolocationByIP(ip)
            cache.set(cache_key, result)
        except urllib2.URLError:
            logging.error("Unable to run getGeolocationByIP()", exc_info=True)
            result = {'lat': 0, 'lng': 0}
    return result



def run_test(ip_addresses):
    if not ip_addresses:
        print "USAGE: %s 87.236.135.147" % __file__
    from time import time
    for ip in ip_addresses:
        t0=time()
        data = getGeolocationByIP(ip)
        t1=time()
        print "Country:".ljust(20), data['country']
        print "City:".ljust(20), data['city']
        print "Lat:".ljust(20), data['lat']
        print "Long:".ljust(20), data['lng']
        print "Took:".ljust(20), (t1-t0), "seconds"

    return 0
if __name__=='__main__':
    import sys
    args = sys.argv[1:]
    sys.exit(run_test(args))
