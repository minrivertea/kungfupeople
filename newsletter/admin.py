# python
import datetime

# django
from django.contrib import admin
from django.utils.timesince import timeuntil
from django.utils.translation import get_date_formats
from django.utils import dateformat


# app
from models import SentLog, Newsletter

(date_format, datetime_format, time_format) = get_date_formats()

class NewsletterAdmin(admin.ModelAdmin):
    
    def save_model(self, request, obj, form, change):
        if request.user.is_superuser:
            obj.author = request.user
        obj.modify_date = datetime.datetime.now()
        obj.save()
        
    list_display = ('send_date_plus', 'sent', 'subject_template', 'author', 'modify_date',
                    'send_count',)
    list_filter = ('language',)
    ordering = ('send_date',)
    exclude = ('add_date', 'modify_date', 'author', 'sent_date')
    
    def sent(self, obj):
        return obj.sent_date is not None
    sent.short_description = "Sent"
    sent.boolean = True
    
    def send_date_plus(self, obj):
        if obj.send_date > datetime.datetime.now():
            return "In " + timeuntil(obj.send_date)
        else:
            return obj.send_date
    send_date_plus.short_description = "Send date"
    
    def send_count(self, obj):
        qs = SentLog.objects.filter(newsletter=obj)
        return "%s/%s" % (qs.filter(sent=True).count(), qs.count())
    send_count.short_description = "Send count"
    
    
admin.site.register(Newsletter, NewsletterAdmin)    
    

    