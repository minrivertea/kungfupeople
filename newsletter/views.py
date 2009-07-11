# python
import datetime

# django
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.db import transaction
from django.template import RequestContext

# app
from models import Newsletter
from forms import PreviewNewsletterForm

def render(request, template, context_dict=None, **kwargs):
    return render_to_response(
        template, context_dict or {}, context_instance=RequestContext(request),
                              **kwargs
    )


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
    
    
def preview(request, newsletter_id):
    newsletter = get_object_or_404(Newsletter, id=newsletter_id)
    person_id = request.GET.get('person')
    
    if person_id:
        form = PreviewNewsletterForm(request.GET)
        if form.is_valid():
            person = form.cleaned_data['person']
            data = {'person': person}
            data.update(newsletter.preview(person))
            
            if data.get('html'):
                # special lazy trick
                request.session['html_preview'] = data['html']
                
            return render(request, 'preview.html', data)
        else:
            return HttpResponse(str(form.errors))
    else:
        form = PreviewNewsletterForm()
        return render(request, 'choose_person.html', {'form':form})
    
def iframe_preview(request, newsletter_id):
    
    html = request.session.get('html_preview')
    if not html:
        return HttpResponse('No HTML prepared for preview :(')
    else:
        return HttpResponse(html)
    