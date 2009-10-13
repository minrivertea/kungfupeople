# python
import logging

# django
from django.contrib import admin
from django.utils.translation import get_date_formats
from django.utils import dateformat

from sorl.thumbnail.main import DjangoThumbnail, get_thumbnail_setting
from sorl.thumbnail.processors import dynamic_import, get_valid_options
thumbnail_processors = dynamic_import(get_thumbnail_setting('PROCESSORS'))

# app
from models import KungfuPerson, Club, DiaryEntry, Style, Photo


(date_format, datetime_format, time_format) = get_date_formats()

class KungfuPersonAdmin(admin.ModelAdmin):
    list_display = ('user', 'join_date', 'full_name', 'email', 'profile_views', 'mugshot')
    
    def join_date(self, obj):
        return dateformat.format(obj.user.date_joined, datetime_format)
    
    def full_name(self, object_):
        return "%s %s" % (object_.user.first_name, object_.user.last_name)
    
    def email(self, object_):
        return object_.user.email
    
    def mugshot(self, obj):
        if not obj.photo:
            return ''
        
        relative_source = obj.photo
        requested_size = (40, 40)
        opts = []
        try:
            thumbnail = DjangoThumbnail(relative_source, requested_size,
                                    opts=opts, 
                                    processors=thumbnail_processors, 
                                    **{})
            thumbnail_url = thumbnail.absolute_url
        except:
            logging.error('grr', exc_info=True)
            return 'error'
        
        return '<img src="%s"/>' % thumbnail_url
    mugshot.short_description = "Photo"
    mugshot.allow_tags = True
    

class ClubAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'url', 'date_added', 'slug')
    ordering = ('date_added', 'name')    

class StyleAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'date_added', 'slug')
    ordering = ('date_added', 'name')

class DiaryEntryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_display = ('title', 'user', 'date_added')
    ordering = ('-date_added',)


class PhotoAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'user', 'date_added',)
    ordering = ('-date_added',)    

    def thumbnail(self, object_):
        relative_source = object_.photo
        requested_size = (40, 40)
        opts = []
        try:
            thumbnail = DjangoThumbnail(relative_source, requested_size,
                                    opts=opts, 
                                    processors=thumbnail_processors, 
                                    **{})
            thumbnail_url = thumbnail.absolute_url
        except:
            logging.error('grr', exc_info=True)
            return 'error'
            
        return '<img src="%s"/>' % thumbnail_url
    
    thumbnail.short_description = u'Thumbnail'
    thumbnail.allow_tags = True

admin.site.register(KungfuPerson, KungfuPersonAdmin)
admin.site.register(Club, ClubAdmin)
admin.site.register(Style, StyleAdmin)
admin.site.register(DiaryEntry, DiaryEntryAdmin)
admin.site.register(Photo, PhotoAdmin)
