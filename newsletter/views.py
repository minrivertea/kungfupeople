# python
import datetime

# django
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db import transaction

# app
from models import Newsletter


@transaction.commit_on_success # ONLY WHEN DEBUGGING
def send_unsent(request, newsletter_id=None):
    
    max_sendouts = int(request.GET.get('max_sendouts', 100))
    
    if newsletter_id:
        newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    else:
        newsletter = None
        newsletters = Newsletter.objects.filter(send_date__lte=datetime.datetime.now(),
                                                sent_date__isnull=True)
        for newsletter in newsletters[:1]:
            break
    
        
    if not newsletter:
        response = "No newsletter to send"
        for newsletter in Newsletter.objects.filter(sent_date__isnull=True,
                                                    send_date__gt=datetime.datetime.now()
                                                    ).order_by('send_date'):
            response += "\nNext one to be sent %s" % \
              newsletter.send_date.strftime('%d %b %Y, %H:%M:%S')
            break

        return HttpResponse(response, mimetype="text/plain")
    
        
    no_sent, left_to_send = newsletter.send(max_sendouts)
    print no_sent, left_to_send
        
    response = "Sent %s" % no_sent
    if left_to_send:
        response += " (%s left to send)" % left_to_send
    
    return HttpResponse(response)
    
    
