# Create your views here.

from django.utils import simplejson
from django.conf import settings

from djangopeople.models import Club, KungfuPerson, Style, Country
from djangopeople.utils import render, render_basic
from django.views.decorators.cache import cache_page, never_cache


if settings.DEBUG:
    def cache_page(delay):
        def rendered(view):
            def inner(request, *args, **kwargs):
                return view(request, *args, **kwargs)
            return inner
        return rendered
    
@cache_page(60 * 60 * 1) # 1 hours                   
def competitions(request):
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

        
    return render(request, 'competitions.html', locals())

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