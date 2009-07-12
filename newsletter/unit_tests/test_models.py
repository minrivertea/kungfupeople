import re
import datetime

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.core import mail

from djangopeople.models import KungfuPerson, Country, AutoLoginKey
from newsletter.models import Newsletter, SentLog, NewsletterTemplateError

from testbase import TestCase

class ModelTestCase(TestCase):
    
    def test_send_newsletter_basic(self):
        """ create a newsletter, set a template text and render it """
        # Create a KungfuPerson so it can send to someone
        user, person = self._create_person('bob', 'bob@example.com',
                                           first_name="Bob",
                                           last_name="Sponge")
    
        text_template = "Hi, {{ first_name }}"
        subject_template = "Newsletter no {{ newsletter_issue_no }}"
        n = Newsletter.objects.create(text_template=text_template,
                                      subject_template=subject_template)
        
        self.assertFalse(n.sent)
        n.send()
        self.assertTrue(n.sent)
        self.assertEqual(n.sent_date.strftime('%Y%m%d%H%M'),
                         datetime.datetime.now().strftime('%Y%m%d%H%M'))
        
        # it should now have sent an email to bob@example.com
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, u"Newsletter no 1")
        self.assertEqual(sent_email.body, u"Hi, Bob")
        self.assertEqual(sent_email.to, ["bob@example.com"])
        
        # it should also have created a SentLog object
        self.assertEqual(SentLog.objects.all().count(), 1)
        sent_log = SentLog.objects.all()[0]
        
        self.assertEqual(sent_log.user, user)
        self.assertEqual(sent_log.subject, u"Newsletter no 1")
        self.assertEqual(sent_log.send_date.strftime('%H%M'),
                         datetime.datetime.now().strftime('%H%M'))
        self.assertEqual(sent_log.to, "bob@example.com")
        
        
    def test_send_newsletter_urls(self):
        """ create a newsletter, set a template text and render it """
        # Create a KungfuPerson so it can send to someone
        user, person = self._create_person('bob', 'bob@example.com',
                                           first_name="Bob",
                                           last_name="Sponge")
    
        text_template = "Profile URL: {{ profile_url }}\n"\
                        "Site URL: {{ site_url }}\n"\
                        "Autologin Profile URL: {{ profile_url_alu }}\n"\
                        "Autologin Site URL: {{ site_url_alu }}\n"
        
        subject_template = "Newsletter no {{ newsletter_issue_no }}"
        n = Newsletter.objects.create(text_template=text_template,
                                      subject_template=subject_template)
        
        self.assertFalse(n.sent)
        n.send()
        
        sent_email = mail.outbox[0]
        # The body of the email should now contain full URLs
        # to the profile and to the site
        site_url_base = 'http://' + Site.objects.get_current().domain
        self.assertTrue((site_url_base + '/') in sent_email.body)
        self.assertTrue((site_url_base + person.get_absolute_url()) in sent_email.body)
        
        # the body should also contain "alu urls", e.g.
        # http://example.com/peterbe?alu=550269bc-bc67-4085-ba1a-04f3f0290288
        alu_regex = re.compile(r'alu=([\w-]{36,})\b')
        uuids = alu_regex.findall(sent_email.body)
        self.assertEqual(len(uuids), 2)
        # but they should be equal
        self.assertEqual(uuids[0], uuids[1])
        # with these it should be possible to get the user back
        self.assertEqual(user,
                         AutoLoginKey.find_user_by_uuid(uuids[0]))
        
    def test_send_newsletter_creation_without_text(self):
        """shouldn't be able to send a Newsletter without text_template or 
        html_text_template"""
        # Create a KungfuPerson so it can send to someone
        user, person = self._create_person('bob', 'bob@example.com',
                                           first_name="Bob",
                                           last_name="Sponge")
    
        subject_template = "Newsletter no {{ newsletter_issue_no }}"
        n = Newsletter.objects.create(subject_template=subject_template)
        
        self.assertRaises(NewsletterTemplateError, n.send)
        
    def test_sending_in_batches(self):
        """create 100 users, send the newsletter but only to 10 people at a 
        time.
        """
        
        # create 100 people
        from string import lowercase, uppercase
        for i in range(100):
            username = "bob%s" % i
            email = "%s@example.com"
            first_name = lowercase[i%25]
            last_name = uppercase[i%25]            
            user, person = self._create_person(username, email,
                                               first_name=first_name,
                                               last_name=last_name)
            
        # create a simple newsletter
        text_template = "Profile URL: {{ profile_url }}"
        subject_template = "Newsletter no {{ newsletter_issue_no }}"
        n = Newsletter.objects.create(text_template=text_template,
                                      subject_template=subject_template)
        n.send(max_sendouts=10)
        self.assertFalse(bool(n.sent_date))
        self.assertFalse(n.sent)
        self.assertEqual(len(mail.outbox), 10)
        
        # and it should have created 10 SentLog items
        self.assertEqual(SentLog.objects.count(), 10)
        
        # send another 20
        n.send(max_sendouts=20)
        self.assertFalse(n.sent)
        self.assertEqual(len(mail.outbox), 30)
        self.assertEqual(SentLog.objects.count(), 30)
        
        # send the rest
        n.send(max_sendouts=9999)
        self.assertTrue(n.sent)
        self.assertEqual(len(mail.outbox), 100)
        self.assertEqual(SentLog.objects.count(), 100)
        
        
    def test_send_newsletter_in_html(self):
        """ create a newsletter, set a template text and render it """
        # Create a KungfuPerson so it can send to someone
        user, person = self._create_person('bob', 'bob@example.com',
                                           first_name="Bob",
                                           last_name="Sponge")
    
        text_template = "" # note! Blank
        html_text_template = "Hi, <strong>{{ first_name }}</strong>\n"\
                             'Visit <a href="{{ site_url }}">us</a>'
        
        subject_template = "Newsletter no {{ newsletter_issue_no }}"
        n = Newsletter.objects.create(html_text_template=html_text_template,
                                      subject_template=subject_template)
        
        n.send()
        sent_email = mail.outbox[0]
        
        # this email should now be a multipart email with a
        # plaintext part and a HTML part
        self.assertTrue(sent_email.message().is_multipart())
        #print dir(sent_email.message())
        
    def test__get_context_for_person(self):
        """ test the context that it generated for a person in a newsletter.
        
        To test, check the private method:
          _get_context_for_person(person, last_send_date=None)
          
        """
        
        user, person = self._create_person('bob', 'bob@example.com',
                                           first_name="Bob",
                                           last_name="Sponge")
    
        text_template = "Bla bla"
        subject_template = "Newsletter no {{ newsletter_issue_no }}"
        n = Newsletter.objects.create(text_template=text_template,
                                      subject_template=subject_template)
        
        context = n._get_context_for_person(person)
        
        self.assertEqual(context['first_name'], u"Bob")
        self.assertEqual(context['last_name'], u"Sponge")
        self.assertEqual(context['email'], "bob@example.com")
        self.assertEqual(context['username'], "bob")
        self.assertEqual(context['profile_views'], 0)
        self.assertNotEqual(context['profile_url'], person.get_absolute_url())
        # but...
        self.assertTrue(context['profile_url'].endswith(person.get_absolute_url()))
        self.assertTrue(context['opt_out_url'].endswith(person.get_absolute_url()+'opt-out/'))
        
        
