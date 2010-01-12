# python
import os
import re
import base64
from urlparse import urlparse
import tempfile

# django
from django import forms
from django.forms.forms import BoundField
from django.db.models import ObjectDoesNotExist
from django.conf import settings

from groupedselect import GroupedChoiceField
from models import KungfuPerson, Country, Region, User, RESERVED_USERNAMES, Club, DiaryEntry, Photo

from youtube import YouTubeVideoError, get_youtube_video_by_id, video_url_or_id
from utils import is_jpeg


try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    import warnings
    warnings.warn("BeautifulSoup not installed (easy_install BeautifulSoup)")
    BeautifulSoup = None

def region_choices():
    # For use with GroupedChoiceField
    regions = list(Region.objects.select_related().order_by('country', 'name'))
    groups = [(False, (('', '---'),))]
    current_country = False
    current_group = []
    
    for region in regions:
        if region.country.name != current_country:
            if current_group:
                groups.append((current_country, current_group))
                current_group = []
            current_country = region.country.name
        current_group.append((region.code, region.name))
    if current_group:
        groups.append((current_country, current_group))
        current_group = []
    
    return groups

def not_in_the_atlantic(self):
    if self.cleaned_data.get('latitude', '') and self.cleaned_data.get('longitude', ''):
        lat = self.cleaned_data['latitude']
        lon = self.cleaned_data['longitude']
        if 43 < lat < 45 and -39 < lon < -33:
            raise forms.ValidationError("Drag and zoom the map until the crosshair matches your location")
    return self.cleaned_data['location_description']

class SignupForm(forms.Form):

    # Fields for creating a User object
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField()
    username = forms.RegexField('^[a-zA-Z0-9_-]+$', min_length=3, max_length=30)
    password1 = forms.CharField(widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(widget=forms.PasswordInput, required=False)
    
    # Fields for creating a KungfuPerson profile
    style = forms.CharField(max_length=200, required=False)

    # Fields for adding a club membership
    club_url = forms.CharField(max_length=200, required=False)
    club_name = forms.CharField(max_length=200, required=False)
    
    country = forms.ChoiceField() # choices loaded later
    latitude = forms.FloatField(min_value=-90, max_value=90)
    longitude = forms.FloatField(min_value=-180, max_value=180)
    location_description = forms.CharField(max_length=50)
    
    region = GroupedChoiceField(required=False) # choices loaded later
    
    initial_user_id = forms.IntegerField(required=False,
                                         widget=forms.widgets.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields['country'].choices = [('', '')] + [
          (c.iso_code, c.name) for c in Country.objects.all()]
        self.fields['region'].choices = region_choices()
    
    # Upload a photo is a separate page, because if validation fails we 
    # don't want to tell them to upload it all over again
    #   photo = forms.ImageField(required=False)
    
    # Fields used to create machinetags
    
    # Validation
    def clean_password1(self):
        "Only required if NO openid set for this form"
        if not self.cleaned_data.get('password1', ''):
            raise forms.ValidationError('Password is required')
        return self.cleaned_data['password1']
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data.get('password2', '')
        if password1.strip() and password1 != password2:
            raise forms.ValidationError('Passwords must match')
        return self.cleaned_data['password2']
    
    def clean_username(self):
        already_taken = 'That username is unavailable'
        username = self.cleaned_data['username'].lower()
        
        # No reserved usernames, or anything that looks like a 4 digit year 
        if username in RESERVED_USERNAMES or (len(username) == 4 and username.isdigit()):
            raise forms.ValidationError(already_taken)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        else:
            try:
                user.get_profile()
                raise forms.ValidationError(already_taken)
            except KungfuPerson.DoesNotExist:
                pass
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email = email)
        except User.DoesNotExist:
            pass
        else:
            raise forms.ValidationError('That e-mail is already in use')
        return email
    
    def clean_region(self):
        # If a region is selected, ensure it matches the selected country
        if self.cleaned_data['region']:
            try:
                region = Region.objects.get(
                    code = self.cleaned_data['region'],
                    country__iso_code = self.cleaned_data['country']
                )
            except ObjectDoesNotExist:
                raise forms.ValidationError(
                    'The region you selected does not match the country'
                )
        return self.cleaned_data['region']

    clean_location_description = not_in_the_atlantic
    
    
    def clean_first_name(self):
        if self.cleaned_data['first_name']:
            v = self.cleaned_data['first_name']
            if v.islower() or v.isupper():
                self.cleaned_data['first_name'] = v.title()
        return self.cleaned_data['first_name']

    def clean_last_name(self):
        if self.cleaned_data['last_name']:
            v = self.cleaned_data['last_name']
            if v.islower() or v.isupper():
                self.cleaned_data['last_name'] = v.title()
        return self.cleaned_data['last_name']


class PhotoUploadForm(forms.Form):
    photo = forms.ImageField()
    description = forms.CharField(widget=forms.Textarea, required=False)
    diary_entry = forms.IntegerField(required=False,
                                     widget=forms.widgets.Select()
                                    )

    country = forms.ChoiceField(required=False)
    latitude = forms.FloatField(required=False, min_value=-90, max_value=90)
    longitude = forms.FloatField(required=False, min_value=-180, max_value=180)
    location_description = forms.CharField(required=False, max_length=50)
    region = GroupedChoiceField(required=False)
    
    def __init__(self, *args, **kwargs):
        super(PhotoUploadForm, self).__init__(*args, **kwargs)
        self.fields['country'].choices = [('', '')] + [
          (c.iso_code, c.name) for c in Country.objects.all()]
        self.fields['region'].choices = region_choices()
    
    
    def clear_diary_entry(self):
        if self.cleaned_data['diary_entry']:
            # check that it's valid
            try:
                DiaryEntry.objects.get(id=self.cleaned_data['diary_entry'])
            except DiaryEntry.DoesNotExist:
                raise forms.ValidationError("Invalid diary entry")
            # but we can't check who it belongs to :(
        self.cleaned_data['diary_entry']
            

class PhotoEditForm(forms.Form):
    description = forms.CharField(widget = forms.Textarea)
    #diary_entry = forms.IntegerField(required=False,
    #                                 widget=forms.widgets.Select()
    #                                )
    diary_entry = forms.ChoiceField(required=False)

    country = forms.ChoiceField(required=False)
    latitude = forms.FloatField(required=False, min_value=-90, max_value=90)
    longitude = forms.FloatField(required=False, min_value=-180, max_value=180)
    location_description = forms.CharField(required=False, max_length=50)
    
    region = GroupedChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(PhotoEditForm, self).__init__(*args, **kwargs)
        self.fields['country'].choices = [('', '')] + [
          (c.iso_code, c.name) for c in Country.objects.all()]
        self.fields['region'].choices = region_choices()
        #self.fields['diary_entry'].choices = diary_entry_choices()


class ProfilePhotoUploadForm(forms.Form):
    photo = forms.ImageField()

class ProfilePhotoWebcamForm(forms.Form):
    image_data = forms.CharField(widget=forms.widgets.HiddenInput())
    
    def clean_image_data(self):
        v = self.cleaned_data['image_data']
        tmp_file_path = os.path.join(tempfile.mkdtemp(), 'webcam.jpg')
        open(tmp_file_path, 'wb').write(base64.b64decode(v))
        if not is_jpeg(tmp_file_path):
            raise forms.ValidationError("Not valid JPEG file")
        else:
            os.remove(tmp_file_path)
        return self.cleaned_data['image_data']
    

class DiaryEntryForm(forms.Form):
    title = forms.CharField(max_length=200, widget=forms.widgets.TextInput(attrs=dict(size=40)))
    content = forms.CharField(widget = forms.Textarea)
    country = forms.ChoiceField(required=False)
    latitude = forms.FloatField(required=False, min_value=-90, max_value=90)
    longitude = forms.FloatField(required=False, min_value=-180, max_value=180)
    location_description = forms.CharField(required=False, max_length=50)
    region = GroupedChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super(DiaryEntryForm, self).__init__(*args, **kwargs)
        self.fields['country'].choices = [('', '')] + [
          (c.iso_code, c.name) for c in Country.objects.all()]
        self.fields['region'].choices = region_choices()

    def clean_region(self):
        # If a region is selected, ensure it matches the selected country
        if self.cleaned_data['region']:
            try:
                region = Region.objects.get(
                    code = self.cleaned_data['region'],
                    country__iso_code = self.cleaned_data['country']
                )
            except ObjectDoesNotExist:
                raise forms.ValidationError(
                    'The region you selected does not match the country'
                )
        return self.cleaned_data['region']
    
    clean_location_description = not_in_the_atlantic

class LocationForm(forms.Form):
    country = forms.ChoiceField()
    latitude = forms.FloatField(min_value=-90, max_value=90)
    longitude = forms.FloatField(min_value=-180, max_value=180)
    location_description = forms.CharField(max_length=50)
    
    region = GroupedChoiceField(required=False)#, choices=region_choices())    
    
    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        self.fields['country'].choices = [('', '')] + [
          (c.iso_code, c.name) for c in Country.objects.all()]
        self.fields['region'].choices = region_choices()
        
    
    def clean_region(self):
        # If a region is selected, ensure it matches the selected country
        if self.cleaned_data['region']:
            try:
                region = Region.objects.get(
                    code = self.cleaned_data['region'],
                    country__iso_code = self.cleaned_data['country']
                )
            except ObjectDoesNotExist:
                raise forms.ValidationError(
                    'The region you selected does not match the country'
                )
        return self.cleaned_data['region']
    
    clean_location_description = not_in_the_atlantic


class ProfileForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.person = kwargs.pop('person', None) # So we can validate e-mail later
        super(ProfileForm, self).__init__(*args, **kwargs)

    bio = forms.CharField(widget = forms.Textarea, required=False)
    club_url = forms.URLField(required=False)
    club_name = forms.CharField(max_length=200, required=False)
    what_is_kungfu = forms.CharField(max_length=144, required=False)
    email = forms.EmailField(required=False)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email = email).exclude(kungfuperson = self.person).count():
            raise forms.ValidationError('That e-mail is already being used') 
        return email

class ClubForm(forms.Form):
    """Now that there is an autocomplete feature that automatically figures out
    the name by the url or the url by the name, we can relax a bit more about
    trying to be convenient on the server-side of things.
    We just can't accept clubs without name so the form is going to have to 
    require it. However, the URL is now no longer required. Basically, we let
    clubs exist without a URL.
    """
    club_name = forms.CharField(max_length=200,
                                widget=forms.widgets.TextInput(attrs=dict(size=40)))
    club_url = forms.URLField(max_length=200, required=False,
                              widget=forms.widgets.TextInput(attrs=dict(size=40)))
    
    def clean_club_url(self):
        url = self.cleaned_data['club_url']
        
        if not url and self.cleaned_data['club_name']:
            try:
                url = Club.objects.get(name__iexact=self.cleaned_data['club_name']).url
            except Club.DoesNotExist:
                pass
        
        if not url.startswith('http://'):
            url = 'http://' + url
            
        # what constitues a valid URL?
        # it's expected to have a protocol and at this point, what other 
        # protocol could we possibly accept except http?
        if not urlparse(url)[0] == 'http':
            raise forms.ValidationError("URL has to start with http://")
        
        # there has to be a domain
        if not urlparse(url)[1]:
            raise forms.ValidationError("No domain name")
        
        # lastly, do a HEAD request and check that the website exists
        if not settings.OFFLINE_MODE:
            import httplib, socket
            conn = httplib.HTTPConnection(urlparse(url)[1])
            try:
                conn.request("HEAD", urlparse(url)[2])
            except socket.gaierror:
                raise forms.ValidationError("Unable to connect to URL")
            res = conn.getresponse()
            if res.status == 200 or (str(res.status).startswith('30') and len(str(res.status)) == 3):
                pass
            else:
                raise forms.ValidationError("Unable to connect to URL (%s)" % res.reason)
                
        return url

        

class StyleForm(forms.Form):
    style_name = forms.CharField(max_length=200)

class VideoForm(forms.Form):
    youtube_video_id = forms.CharField(required=False,
                                      widget=forms.widgets.TextInput(attrs=dict(size=36)))
    title = forms.CharField(required=True, 
                            widget=forms.widgets.TextInput(attrs=dict(size=36)))    
    
    embed_src = forms.CharField(widget=forms.Textarea, required=False)
    description = forms.CharField(widget=forms.Textarea, required=False)
    
    thumbnail_url = forms.CharField(required=False,
                                    widget=forms.widgets.HiddenInput())
    
    def clean_embed_src(self):
        embed_src = self.cleaned_data['embed_src']
        
        # check the tags it's allowed to contain
        allowed_tags = ('object', 'embed', 'param')
        for tag in re.findall(r'<(\w+)[^>]*>', embed_src):
            if tag not in allowed_tags:
                raise forms.ValidationError("Tag not allowed (<%s>)" % tag)
            
        from HTMLParser import HTMLParseError
        try:
            soup = BeautifulSoup(embed_src.strip())
        except HTMLParseError:
            raise forms.ValidationError("HTML too broken to be parsed")
            
        self.cleaned_data['embed_src'] = str(soup)
        return self.cleaned_data['embed_src']
    
    def clean_youtube_video_id(self):
        video_id = self.cleaned_data['youtube_video_id'].strip()
        if video_id:
            try:
                video_id = video_url_or_id(video_id)
            except YouTubeVideoError, msg:
                raise forms.ValidationError(str(msg))
            
        return video_id


def make_validator(key, form):
    def check():
        if form.cleaned_data.get(key.replace('url_', 'title_')) and \
            not form.cleaned_data.get(key):
            raise forms.ValidationError, 'You need to provide a URL'
        return form.cleaned_data.get(key)
    return check


class NewsletterOptionsForm(forms.Form):
    
    newsletter = forms.CharField(max_length=5, required=False,
                                widget=forms.widgets.RadioSelect(choices=KungfuPerson.NEWSLETTER_CHOICES))
    
    


class CropForm(forms.Form):
     x1 = forms.IntegerField()
     y1 = forms.IntegerField()
     x2 = forms.IntegerField()
     y2 = forms.IntegerField()
     w = forms.IntegerField()
     h = forms.IntegerField()
     
     def __init__(self, *args, **kwargs):
         super(CropForm, self).__init__(*args, **kwargs)
         for field in self.fields:
             self.fields[field].widget = forms.widgets.HiddenInput()
             
     
