import datetime
from django.contrib.sites.models import RequestSite
from django.contrib.sites.models import Site
from django.contrib.sitemaps import Sitemap as DjangoSitemap
from django.utils.encoding import smart_str
from django.template import loader
from django.http import HttpResponse, Http404
from django.core.paginator import EmptyPage, PageNotAnInteger

from djangopeople.models import Country, Region, Club, Style, DiaryEntry, \
  Photo, Video, KungfuPerson

def sitemap(request, sitemaps, section=None):
    maps, urls = [], []
    if section is not None:
        if section not in sitemaps:
            raise Http404("No sitemap available for section: %r" % section)
        maps.append(sitemaps[section])
    else:
        maps = sitemaps.values()
    page = request.GET.get("p", 1)
    for site in maps:
        site.request = request
        try:
            if callable(site):
                urls.extend(site().get_urls(page))
            else:
                urls.extend(site.get_urls(page))
        except EmptyPage:
            raise Http404("Page %s empty" % page)
        except PageNotAnInteger:
            raise Http404("No page '%s'" % page)
    xml = smart_str(loader.render_to_string('sitemap.xml', {'urlset': urls}))
    return HttpResponse(xml, mimetype='application/xml')    


class Sitemap(DjangoSitemap):

    def get_urls(self, page=1):
        current_site = RequestSite(self.request)
        urls = []
        for item in self.paginator.page(page).object_list:
            loc = "http://%s%s" % (current_site.domain, self.__get('location', item))
            url_info = {
                'location':   loc,
                'lastmod':    self.__get('lastmod', item, 
                                         getattr(item, 'lastmod', None)),
                'changefreq': self.__get('changefreq', item, 
                                         getattr(item, 'changefreq', None)),
                'priority':   self.__get('priority', item, 
                                         getattr(item, 'priority', None))
            }
            urls.append(url_info)
        return urls


class Page(object):
    
    def __init__(self, location, changefreq=None):
        self.location = location
        self.changefreq = changefreq
    
    def get_absolute_url(self):
        return self.location
    

    
class CustomSitemap(Sitemap):
    #def location(self, obj):
    #    return obj['location']
    
    def items(self):
        all = []
        all += [
                Page("/",
                     changefreq="daily",
                    ),
                #Page("/statistics/calendar/",
                #     changefreq="weekly",
                #     ),
                # 
                #Page("/statistics/graph/",
                #     changefreq="weekly",
                #     ),
                #Page("/statistics/uniqueness/",
                #     changefreq="weekly",
                #     ),
                #Page("/word-whomp/",
                #     changefreq="weekly",
                #     ),
                #Page("/crossing-the-world/",
                #     changefreq="daily",
                #     ),                
                ]
        
        
        country_iso_codes = set()
        
        # Add all the profiles
        today = datetime.datetime.now()
        for person in KungfuPerson.objects.all().order_by('-user__date_joined'):
            changefreq = 'weekly'
            if ((today - person.user.last_login).days) < 7:
                changefreq = 'daily'
            all.append(Page(person.get_absolute_url(), changefreq=changefreq))
            country_iso_codes.add(person.country.iso_code)
            
        # All photos
        for photo in Photo.objects.all().order_by('-date_added'):
            changefreq = 'monthly'
            age = (today - photo.date_added).days
            if age < 7:
                changefreq = 'daily'
            elif age < 30:
                changefreq = 'weekly'
            all.append(Page(photo.get_absolute_url(), changefreq=changefreq))
            
        # All diary entries
        for entry in DiaryEntry.objects.filter(is_public=True).order_by('-date_added'):
            changefreq = 'monthly'
            age = (today - entry.date_added).days
            if age < 7:
                changefreq = 'daily'
            elif age < 30:
                changefreq = 'weekly'
            all.append(Page(entry.get_absolute_url(), changefreq=changefreq))
            
        # All clubs
        for club in Club.objects.all():
            changefreq = 'weekly'
            all.append(Page(club.get_absolute_url(), changefreq=changefreq))
            
        # All styles
        for style in Style.objects.all():
            changefreq = 'weekly'
            all.append(Page(style.get_absolute_url(), changefreq=changefreq))
            
        # All countries
        for iso_code in country_iso_codes:
            changefreq = 'monthly'
            all.append(Page('/%s/' % iso_code.lower(), changefreq=changefreq))
            
            
        return all


class FlatPageSitemap(Sitemap):
    def items(self):
        current_site = Site.objects.get_current()
        return current_site.flatpage_set.all()
