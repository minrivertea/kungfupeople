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
    ordering = ('-send_date',)
    exclude = ('date_added', 'author', 'sent_date')
    
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
    
    
    def change_view(self, request, object_id, extra_context={}):
        
        from djangopeople.models import KungfuPerson
        
        #frock = Frock.objects.get(corefrock__pk=object_id)
        #frock_of_the_week = get_frock_of_the_week()
        #extra_context = {'frock': frock, 'frock_of_the_week': frock_of_the_week}
        newsletter = Newsletter.objects.get(pk=object_id)
        sent_logs = SentLog.objects.filter(newsletter=newsletter)
        count_sent = sent_logs.count()
        extra_context.update(dict(count_sent=count_sent,
                                  newsletter=newsletter))
        if count_sent:
            extra_context['count_sent_failed'] = \
              sent_logs.filter(sent=False).count()
        else:
            extra_context['will_send_html'] = \
              KungfuPerson.objects.filter(newsletter='html').count()
            extra_context['will_send_plain'] = \
              KungfuPerson.objects.filter(newsletter='plain').count()
            extra_context['will_send_total'] = \
              extra_context['will_send_html'] + extra_context['will_send_plain']
            
        return super(NewsletterAdmin, self).change_view(request, object_id, extra_context)
    
    
    
admin.site.register(Newsletter, NewsletterAdmin)
    

    