# django
from django import forms

# app
from djangopeople.models import KungfuPerson

class PreviewNewsletterForm(forms.Form):
    person = forms.ModelChoiceField(KungfuPerson.objects.all().\
      order_by('user__first_name', 'user__last_name'))
    
    
    
    