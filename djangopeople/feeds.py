from django.contrib.syndication.feeds import Feed
from djangopeople.models import KungfuPerson


class LatestPeople(Feed):
    title = "Latest people added"
    link = "/"
    description = "Latest people who have signed up"

    def items(self):
        return KungfuPerson.objects.order_by('-user__date_joined')[:10]
    
            
                        
