#import re
#import datetime

#from django.contrib.auth.models import User
#from django.contrib.sites.models import Site
#from django.test import TestCase
#from django.core import mail

#from djangopeople.models import KungfuPerson, Country, AutoLoginKey
#from newsletter.models import Newsletter, SentLog, NewsletterTemplateError

from testbase import TestCase

from newsletter.templatetags import newsletter_extras

class NewsletterExtrasTestCase(TestCase):
    
    def test_add2url_basic(self):
        """Merge
        'http://www.com/path/?cgi=abc#top'
        with
        'subdirectory/'
        """
        url = "http://www.com/path/?cgi=abc#top"
        add = "subdirectory/"
        rendered = newsletter_extras.add2url(url, add)
        self.assertEqual(rendered,
                         "http://www.com/path/subdirectory/?cgi=abc#top")
        
        url = "/path/?cgi=abc#top"
        add = "subdirectory/"
        rendered = newsletter_extras.add2url(url, add)
        self.assertEqual(rendered,
                         "/path/subdirectory/?cgi=abc#top")
        
    def test_add2url_with_querystring(self):
        """add a query string
        """
        url = "/path/"
        add = "?foo=bar"
        rendered = newsletter_extras.add2url(url, add)
        self.assertEqual(rendered,
                         "/path/?foo=bar")
        
        url = "/path/#top"
        add = "?foo=bar"
        rendered = newsletter_extras.add2url(url, add)
        self.assertEqual(rendered,
                         "/path/?foo=bar#top")
        
        url = "/path/"
        add = "?foo=bar#top"
        rendered = newsletter_extras.add2url(url, add)
        self.assertEqual(rendered,
                         "/path/?foo=bar#top")
        
        url = "/path/?foo=bar"
        add = "#top"
        rendered = newsletter_extras.add2url(url, add)
        self.assertEqual(rendered,
                         "/path/?foo=bar#top")
        
        url = "/path/#bottom"
        add = "?foo=bar#top"
        rendered = newsletter_extras.add2url(url, add)
        self.assertEqual(rendered,
                         "/path/?foo=bar#top")
        

    def test_add2url_in_template(self):
        url = "http://www.com/path/?cgi=abc#top"
        
        template_as_string = """
        {% load newsletter_extras %}
        {{ url|add2url:"subdirectory/" }}
        """
        from django.template import Template
        from django.template import Context
                
        template = Template(template_as_string)
        context = Context({'url':url})
        rendered = template.render(context)
        self.assertEqual(rendered.strip(),
                         "http://www.com/path/subdirectory/?cgi=abc#top")
                
        

