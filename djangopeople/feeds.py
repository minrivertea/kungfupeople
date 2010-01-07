import datetime
from django.conf import settings
from django.contrib.syndication.feeds import Feed
from django.utils.feedgenerator import Atom1Feed

from djangopeople.models import KungfuPerson, Photo, DiaryEntry


THIS_YEAR = datetime.datetime.now().year

class LatestPeople(Feed):
    feed_type = Atom1Feed
    
    title = "%s (Latest people added)" % settings.PROJECT_NAME
    link = "/"
    subtitle = "Latest people who have signed up"
    
    author_name = settings.PROJECT_NAME
    copyright = 'Copyright (c) %s, %s' % (THIS_YEAR, settings.PROJECT_NAME)

    def items(self):
        return KungfuPerson.objects.order_by('-user__date_joined')[:20]
    
    def item_pubdate(self, item):
        return item.user.date_joined
    
    
class LatestAll(Feed):
    """Combining new signups, new photos, new diary entries, ...
    """
    feed_type = Atom1Feed
    
    title = settings.PROJECT_NAME
    subtitle = "All latest activity on %s" % settings.PROJECT_NAME
    
    author_name = settings.PROJECT_NAME
    copyright = 'Copyright (c) %s, %s' % (THIS_YEAR, settings.PROJECT_NAME)

    def items(self):
        items = []
        
        for each in KungfuPerson.objects.order_by('-user__date_joined')[:100]:
            items.append((each.user.date_joined, each))
            
        for each in Photo.objects.order_by('-date_added')[:100]:
            items.append((each.date_added, each))
            
        for each in DiaryEntry.objects.filter(is_public=True).order_by('-date_added')[:100]:
            items.append((each.date_added, each))
            
        items.sort()
        items.reverse()
        return [x[1] for x in items[:20]]
        
        
    
    def item_pubdate(self, item):
        if isinstance(item, DiaryEntry) or isinstance(item, Photo):
            return item.date_added
        elif isinstance(item, KungfuPerson):
            return item.user.date_joined
        else:
            raise ValueError, "Unknown item"
        
            
                        
