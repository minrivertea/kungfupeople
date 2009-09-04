# python
import datetime
import os
import logging
from urlparse import urlparse
import urllib
import hashlib

# django
from django.utils.timesince import timesince
from django.core.cache import cache
from django.conf import settings

# other
from sorl.thumbnail.main import DjangoThumbnail, get_thumbnail_setting
from sorl.thumbnail.processors import dynamic_import, get_valid_options
from django.utils.text import truncate_words
thumbnail_processors = dynamic_import(get_thumbnail_setting('PROCESSORS'))
try:
    from django_static import slimfile, staticfile
except ImportError:
    from django_static.templatetags.django_static import slimfile, staticfile

# app
from models import Club, Style, KungfuPerson, Photo

ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60
ONE_DAY = ONE_HOUR * 24
ONE_WEEK = ONE_DAY * 7
ONE_YEAR = ONE_WEEK * 52

_default_thumbnail_urls = {
    30: '/img/upload-a-photo-30.png',
    40: '/img/upload-a-photo-40.png',
    60: '/img/upload-a-photo-60.png',
}
_media_url = getattr(settings, 'GRAVATAR_MEDIA_URL',
                     getattr(settings, 'DJANGO_STATIC_MEDIA_URL',
                             'http://kungfupeople.com'))
if _media_url.endswith('/'):
    _media_url = _media_url[:-1]
def gravatar_thumbnail_url(email, size=40):
    assert int(size) in (30,40,60), "Invalid thumbnail size %r" % size
    logging.info("media_url=%r" % _media_url)
    default = staticfile(_default_thumbnail_urls[int(size)])
    if default.startswith('/'):
        default = _media_url + default
    return "http://www.gravatar.com/avatar.php?" + \
      urllib.urlencode({'gravatar_id':hashlib.md5(email).hexdigest(),
                        'default':default, 
                        'size':str(size)})


class _ListItem(object):
    __slots__ = ('url','title','info','thumbnail_url', 'thumbnail_size')
    def __init__(self, url, title, info=u'', thumbnail_url='', thumbnail_size=()):
        self.url = url
        self.title = title
        self.info = info
        self.thumbnail_url = thumbnail_url
        self.thumbnail_size = thumbnail_size


def get_all_items(model, sort_by):
    qs = {'clubs': Club,
          'styles': Style,
          'people': KungfuPerson,
          'photos': Photo,
         }[model].objects.all()
    
    if model == 'people':
        qs = qs.select_related('user')
    elif model == 'photos':
        qs = qs.select_related('country','user')

    if sort_by == 'date':
        order_by = {'clubs':'-add_date',
                    'styles':'-add_date',
                    'people':'-user__date_joined',
                    'photos':'-date_added',
                    }[model]
    else: # by name
        order_by = {'clubs':'name',
                    'styles':'name',
                    'people':('user__first_name', 'user__last_name'),
                    'photos':('location_description', 'country__name'),
                    }[model]
    if isinstance(order_by, basestring):
        order_by = (order_by,)
        
    qs = qs.order_by(*order_by)
    
    count = qs.count()
    page_title = u"All %s %s" % (count, model)
    title = "All %s %s on this site so far" % (count, model)
    
    # now, turn this queryset into a list of _ListItems
    _today = datetime.datetime.today()
    
    counts_cache_key = 'all-counts-%s' % model
    counts = cache.get(counts_cache_key, {})
    
    
    items = []
    for item in qs:
        if model == 'people':
            if item.photo:
                thumbnail = DjangoThumbnail(item.photo, (40,40), opts=['crop'],
                                        processors=thumbnail_processors)
                thumbnail_url = thumbnail.absolute_url
            else:
                thumbnail_url = gravatar_thumbnail_url(item.user.email, size=40)
                #thumbnail_url = staticfile('/img/upload-a-photo-40.png')
            thumbnail_size = (40, 40)
            info = 'joined %s ago' % timesince(item.user.date_joined, _today)
            items.append(_ListItem(
                    item.get_absolute_url(),
                    item.user.get_full_name(),
                    info=info,
                    thumbnail_url=thumbnail_url,
                    thumbnail_size=thumbnail_size,
                        ))
        elif model == 'photos':
            if not os.path.isfile(os.path.join(settings.MEDIA_ROOT, item.photo.path)):
                logging.info("Photo id=%s is missing the photo itself!" %\
                             item.id)
                continue
            thumbnail = DjangoThumbnail(item.photo, (40,40), opts=['crop'],
                                        processors=thumbnail_processors)
            thumbnail_url = thumbnail.absolute_url
            thumbnail_size = (40,40)
            if item.description:
                _title = truncate_words(item.description, 10)
            else:
                _title = ''
            _title = ' %s, %s' % (item.location_description, item.country.name)
            #if item.description:
            #    title = truncate_words(item.description, 10)
            #else:
            #    title = ''
            info = 'Added by <a href="/%s/">%s</a>' % (item.user.username, 
                                                         item.user.get_full_name())
            info += ' %s ago' % timesince(item.date_added, _today)
            items.append(_ListItem(
                                   item.get_absolute_url(),
                                   _title.strip(),
                                   info=info,
                                   thumbnail_url=thumbnail_url,
                                   thumbnail_size=thumbnail_size,
                        ))
        elif model in ('clubs','styles'):
            if item.id in counts:
                people_count = counts[item.id]
            else:
                people_count = item.kungfuperson_set.count()
                counts[item.id] = people_count
            if people_count:
                if people_count > 1:
                    info = '%s people' % people_count
                else:
                    info = '1 person'
            else:
                info = 'added %s ago' % timesince(item.add_date, _today)
            items.append(_ListItem(
                    item.get_absolute_url(),
                    item.name,
                    info=info,
                        ))
            
    cache.set(counts_cache_key, counts, ONE_HOUR)
            
    return dict(items=items,
                page_title=page_title,
                title=title)