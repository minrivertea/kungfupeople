from django.contrib.sites.models import Site
from django.test import TestCase
from django.core import mail
from django.contrib.sites.models import Site

from djangopeople.models import KungfuPerson, Country, AutoLoginKey
from newsletter.models import Newsletter, SentLog, NewsletterTemplateError

from testbase import TestCase

class ViewsTestCase(TestCase):
    
    def test_view_newsletter_online(self):
        """ all newsletters that have been gone out are viewable for the 
        person.
        """
        user, person = self._create_person("bob", "bob@example.com", 
                                           password="secret",
                                           first_name=u"Bob",
                                           last_name=u"Sponge")
        
        html_text_template = "<p>Profile URL: {{ profile_url }}</p>"
        subject_template = "Newsletter no {{ newsletter_issue_no }}"
        n = Newsletter.objects.create(html_text_template=html_text_template,
                                      subject_template=subject_template)

        # won't be allowed as you're not logged in
        url = '/newsletters/%s/%s/' % (person.user.username, n.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403) # forbidden
        
        # have to log in
        self.client.login(username="bob", password="secret")
        
        # you're not allowed to view a newsletter that hasn't been sent to you
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        
        n.send()
        
        # now it should be ok
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        domain = Site.objects.get_current().domain
        expected_html = '<p>Profile URL: http://%s%s</p>' % (domain, person.get_absolute_url())
        self.assertTrue(expected_html in response.content)
        
    
    def test_send_unsent(self):
        """going to newsletters/send_unsent/ should send all newsletters"""
        # first create some people to send to 
        from string import lowercase, uppercase
        for i in range(100):
            username = "bob%s" % i
            email = "%s@example.com"
            first_name = lowercase[i%25]
            last_name = uppercase[i%25]            
            self._create_person(username, email,
                                first_name=first_name,
                                last_name=last_name)
            
        # then create a newsletter
        text_template = "Profile URL: {{ profile_url }}"
        subject_template = "Newsletter no {{ newsletter_issue_no }}"
        n = Newsletter.objects.create(text_template=text_template,
                                      subject_template=subject_template)
        
        
        response = self.client.get('/newsletters/send_unsent/?max_sendouts=10')
        assert response.status_code == 200
        self.assertEqual(len(mail.outbox), 10)
        
        self.assertTrue('Sent 10' in response.content)
        self.assertTrue('90 left to send' in response.content)

        response = self.client.get('/newsletters/send_unsent/?max_sendouts=20')
        assert response.status_code == 200
        self.assertEqual(len(mail.outbox), 30)
        
        self.assertTrue('Sent 20' in response.content)
        self.assertTrue('70 left to send' in response.content)

        response = self.client.get('/newsletters/send_unsent/')
        assert response.status_code == 200
        self.assertEqual(len(mail.outbox), 100)
        
        self.assertTrue('Sent 70' in response.content)
        
        response = self.client.get('/newsletters/send_unsent/')
        assert response.status_code == 200
        self.assertEqual(response.content, 'No newsletter to send')
        
        
        
        