import re
import os
import random

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.db import transaction
from django.conf import settings

from newsletter.models import SentLog, Newsletter


class Command(BaseCommand):
    help = """find orphaned frock photos"""
    
    def handle(self, *args, **options):
        
        if not args or (args and not args[0].isdigit()):
            for newsletter in Newsletter.objects.filter(sent_date__isnull=False).order_by('send_date'):
                print "Newsletter ID: %s\t%s" % (newsletter.id, newsletter.sent_date.strftime('%d %b %Y, %H:%M:%S')),
                qs = SentLog.objects.filter(newsletter=newsletter)
                print "\t%s/%s" % (qs.filter(sent=True).count(), qs.count())
            raise CommandError("USAGE: ./manage.py %s <newsletterid>" % \
                               os.path.basename(__file__).split('.')[0])
        
        newsletter_id = args[0]
        
        transaction.enter_transaction_management()
        transaction.managed(True)
        
        newsletter = Newsletter.objects.get(id=newsletter_id)
        
        newsletter.sent_date = None
        newsletter.save()
        
        SentLog.objects.filter(newsletter=newsletter).delete()
        
        
        transaction.commit()
        #transaction.rollback()
        
