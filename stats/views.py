import re
import datetime
from time import mktime

from django.utils import simplejson
from django.conf import settings

from django.http import Http404
from djangopeople.models import Club, KungfuPerson, Style, Country
from djangopeople.utils import render, render_basic
from django.views.decorators.cache import cache_page, never_cache
from django.core.cache import cache
from django.contrib.auth.models import User
from stats.utils import extract_views_from_urlpatterns

from django.utils.decorators import decorator_from_middleware
from django.middleware.cache import CacheMiddleware
class CustomCacheMiddleware(CacheMiddleware):
    def __init__(self, cache_delay=0, *args, **kwargs):
        super(CustomCacheMiddleware, self).__init__(*args, **kwargs)
        self.cache_delay = cache_delay
        
    def process_response(self, request, response):
        if self.cache_delay:
            extra_js = '<script type="text/javascript">var CACHE_CONTROL=%s;</script>' %\
              self.cache_delay
            response.content = response.content.replace(u'</body>',
                                                        u'%s\n</body>' % extra_js)

        response = super(CustomCacheMiddleware, self).process_response(request, response)
        return response

custom_cache_page = decorator_from_middleware(CustomCacheMiddleware)


if 1 or settings.DEBUG:
    def cache_page(delay):
        def rendered(view):
            def inner(request, *args, **kwargs):
                return view(request, *args, **kwargs)
            return inner
        return rendered
    custom_cache_page = cache_page
    


@custom_cache_page(60 * 60 * 1) # 1 hours
def competitions(request):
    data = dict()
    data.update(_get_competitions_tables())
    return render(request, 'competitions.html', data)
    

def _get_competitions_tables():
    groups = []
    for club in Club.objects.all():
        count = club.kungfuperson_set.count()
        if not count:
            continue
        groups.append({'object':club,
                       'count': count})
    groups.sort(lambda x,y: cmp(y['count'], x['count']))
    clubs_groups_table = _groups_table(groups, 
                                       "Club",
                                       "Members").content
    
    groups = []
    for style in Style.objects.all():
        count = style.kungfuperson_set.count()
        if not count:
            continue
        groups.append({'object': style,
                       'count': count})
    groups.sort(lambda x,y: cmp(y['count'], x['count']))
    styles_groups_table = _groups_table(groups, 
                                       "Style",
                                       "Practioners").content
    
    groups = []
    for country in Country.objects.all():
        count = country.kungfuperson_set.count()
        if not count:
            continue
        groups.append({'object': country,
                       'count': count
                      })
    groups.sort(lambda x,y: cmp(y['count'], x['count']))
    countries_groups_table = _groups_table(groups, 
                                       "Country",
                                       "Citizens").content
    
    groups = []
    for person in KungfuPerson.objects.all():
        count = person.profile_views
        if not count:
            continue
        groups.append({'object': person,
                       'count': count
                      })
    groups.sort(lambda x,y: cmp(y['count'], x['count']))
    profile_views_groups_table = _groups_table(groups,
                                       "Person",
                                       "Profile views").content
    
    # This below is deliberately commented out since the counts were
    # introduced so late to clubs and styles. We'll release this later
    # when the clicks have started to clock up a bit more.
    # /Peter, 31 aug 09
    if 0:
        groups = []
        for club in Club.objects.all():
            count = club.clicks
            if not count:
                continue
            groups.append({'object': club,
                           'count': count})
        groups.sort(lambda x,y: cmp(y['count'], x['count']))
        club_clicks_groups_table = _groups_table(groups,
                                       "Club",
                                       "Clicks").content
        
        groups = []
        for style in Style.objects.all():
            count = style.clicks
            if not count:
                continue
            groups.append({'object': style,
                           'count': count})
        groups.sort(lambda x,y: cmp(y['count'], x['count']))
        style_clicks_groups_table = _groups_table(groups,
                                       "Style",
                                       "Clicks").content        
    
    data = locals()
    del data['groups']
    del data['count']
    return data

        

def _groups_table(groups, column1_label, column2_label, max_groups=10):
    count_total = sum([x['count'] for x in groups])
    restgroup = {}
    for group in groups[max_groups:]:
        if not restgroup:
            restgroup['name'] = "All others"
            restgroup['count'] = 1
        else:
            restgroup['count'] += 1
    groups = groups[:max_groups]
    return render_basic('_groups_table.html', locals())





def index(request):
    """list all available stats pages"""
    return render(request, 'stats-index.html', locals())

@custom_cache_page(60 * 60)
def new_people(request, period='monthly'):
    """page that shows a line graph showing the number of new signups
    cummulativively or individual"""
    #blocks = 'monthly'
    
    weekly = period == 'weekly'
    def _find_week_min_max(date):
        # given a date anywhere in the middle of the week, return the date
        # of that week's Monday at 00:00:00 and return the Monday exactly
        # 7 days later
        search_date = datetime.datetime(date.year, date.month, date.day, 0, 0, 0)
        while search_date.strftime('%A') != 'Monday':
            search_date = search_date - datetime.timedelta(days=1)
            
        return search_date, search_date + datetime.timedelta(days=7)
    
    first_date = User.objects.all().order_by('date_joined')[0].date_joined
    last_date = User.objects.all().order_by('-date_joined')[0].date_joined
    
    buckets = dict()
    
    date = first_date
    qs = User.objects.filter(is_staff=False)
    
    count_previous = 0
    total_count = 0
    while date < last_date:
        if weekly:
            key = date.strftime('%Y%W')
        else:
            # default is monthly
            key = date.strftime('%Y%m')
        if key not in buckets:
            
            
            if weekly:
                week_min, next_week = _find_week_min_max(date)
                this_qs = qs.filter(date_joined__gte=week_min,
                                    date_joined__lt=next_week)
                date_hourless = week_min
            else:
                date_hourless = datetime.date(date.year, date.month, 15)
                this_qs = qs.filter(date_joined__year=date.year,
                                date_joined__month=date.month)
                
            count = this_qs.count()
            total_count += count
            buckets[key] = {'year': date.year, 
                            'month': date.month,
                            'month_name': date.strftime('%B'),
                            'date': date,
                            'count': count,
                            'total_count': total_count,
                            'timestamp': int(mktime(date_hourless.timetuple())) * 1000,
                            }
            if weekly:
                buckets[key]['week_name'] = date.strftime('%W')
            
        date = date + datetime.timedelta(days=1)
        
    # turn it into a list
    buckets = [v for v in buckets.values()]
    buckets.sort(lambda x,y: cmp(x['date'], y['date']))

    buckets_timestamps = [[x['timestamp'], x['count']]
                          for x in buckets]
    buckets_timestamps_json = simplejson.dumps(buckets_timestamps)
    
    buckets_cumulative_timestamps = [[x['timestamp'], x['total_count']]
                          for x in buckets]
    buckets_cumulative_timestamps_json = simplejson.dumps(buckets_cumulative_timestamps)
    
    return render(request, 'stats-new-people.html', locals())
    
    
def list_new_people_html(request):
    try:
        # UTC timestamps
        from_timestamp = float(request.GET.get('from'))
        to_timestamp = float(request.GET.get('to'))
        if from_timestamp > to_timestamp:
            raise Http404("to timestamp less than from")
    except ValueError:
        raise Http404("Invalid timestamps")
    
    from_datetime = datetime.datetime.utcfromtimestamp(from_timestamp/ 1000)
    to_datetime = datetime.datetime.utcfromtimestamp(to_timestamp/ 1000)
    
    print from_datetime, to_datetime
    
    people = KungfuPerson.objects.filter(user__date_joined__gte=from_datetime,
                                         user__date_joined__lt=to_datetime)
    print people.count()
    #print people.query.as_sql()
    people = people.select_related().order_by('user__date_joined')
        
    return render(request, '_list-new-people.html', locals())
