# python
import datetime

# django
from django.contrib import admin
from django.utils.timesince import timeuntil
from django.utils.timesince import timesince

# app
from models import WelcomeEmail

class WelcomeEmailAdmin(admin.ModelAdmin):
    list_display = ('send_date_plus', 'sent', 'subject', 'user', 
                    'delay')
    ordering = ('-send_date',)
    
    def sent(self, obj):
        return obj.send_date is not None
    sent.short_description = "Sent"
    sent.boolean = True
    
    def delay(self, obj):
        if obj.send_date:
            return timesince(obj.user.date_joined, obj.send_date)
        else:
            return "n/a"
        return obj.user.date_joined
    delay.short_description = "Delay"

    def send_date_plus(self, obj):
        if obj.send_date:
            return obj.send_date
        else:
            return "n/a"
    send_date_plus.short_description = "Send date"
    
    
    def changelist_view(self, request, extra_context=None, **kwargs):
        if extra_context is None:
            extra_context = {}
        extra_context['users_to_welcome'] = WelcomeEmail.get_users_to_welcome()
        return super(WelcomeEmailAdmin, self).changelist_view(request, 
                                                              extra_context=extra_context,
                                                              **kwargs)

admin.site.register(WelcomeEmail, WelcomeEmailAdmin)