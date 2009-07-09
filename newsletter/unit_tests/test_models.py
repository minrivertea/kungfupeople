import re
import datetime

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase
from django.core import mail

from djangopeople.models import KungfuPerson, Country, AutoLoginKey
from newsletter.models import Newsletter, SentLog

class ModelTestCase(TestCase):
    
    def _create_person(self, username, email, password="secret", 
                       first_name="", last_name="",
                       country="United Kingdom",
                       region=None,
                       latitude=51.532601866,
                       longitude=-0.108382701874):
        
        user = User.objects.create_user(username=username,
                                        email=email,
                                        password=password)
        if first_name or last_name:
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            
        country = Country.objects.get(name=country)
        person = KungfuPerson.objects.create(user=user,
                                             country=country,
                                             region=region,
                                             latitude=latitude,
                                             longitude=longitude)
        
        return user, person

    
    
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
        
        self.assertFalse(bool(n.send_date))
        n.send()
        self.assertTrue(bool(n.send_date))
        self.assertEqual(n.send_date.strftime('%Y%m%d%H%M'),
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
        self.assertEqual(sent_log.text, u"Hi, Bob")
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
        
        self.assertFalse(bool(n.send_date))
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
        
