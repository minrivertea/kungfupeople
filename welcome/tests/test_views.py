# python
import datetime

# django
from django.core import mail
from django.conf import settings
from django.core.urlresolvers import reverse

from djangopeople.unit_tests.testbase import TestCase
from djangopeople.models import Style, Club
from welcome.models import WelcomeEmail

class ViewsTestCase(TestCase):
    def test_create_welcome_emails(self):
        response = self.client.get('/welcome/create-welcome-emails/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'No welcome emails this time')
        
        # create a user
        user, person = self._create_person('bob', 'bob@example.com',
                                           first_name=u"Bob",
                                           last_name="Ippo")
        response = self.client.get('/welcome/create-welcome-emails/')
        self.assertEqual(response.status_code, 200)
        # the reason we expect nothing to be sent is because the user joined
        # too recently
        self.assertEqual(response.content, 'No welcome emails this time')

        last_week = datetime.datetime.now() - datetime.timedelta(days=7)
        user.date_joined = last_week
        user.save()
        response = self.client.get('/welcome/create-welcome-emails/')
        self.assertEqual(response.status_code, 200)
        # if the user signed up a long time ago no welcome email should be
        # sent
        self.assertEqual(response.content, 'No welcome emails this time')
        
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        user.date_joined = yesterday
        user.save()
        response = self.client.get('/welcome/create-welcome-emails/')
        self.assertEqual(response.status_code, 200)
        # if the user signed up a long time ago no welcome email should be
        # sent
        self.assertEqual(response.content, 'Created 1 welcome email')
        
        welcome_email = WelcomeEmail.objects.get(user=user)
        # the subject line should have PROJECT_NAME in it
        self.assertTrue(welcome_email.subject.count(settings.PROJECT_NAME))
        # this is copied from the user for auditing purposes
        self.assertEqual(welcome_email.email, 'bob@example.com')
        
        # the body of the email should mention the first name
        self.assertTrue(welcome_email.body.count(u"Bob"))
        
        # somewhere in the body should be a link to the profile page
        profile_url = reverse('person.view', args=('bob',))
        self.assertTrue(welcome_email.body.count(profile_url))
        edit_password_url = reverse('edit_password', args=('bob',))
        self.assertTrue(welcome_email.body.count(edit_password_url))
        # since the user hasn't uploaded a photo
        upload_photo_url = reverse('upload_photo', args=('bob',))
        self.assertTrue(welcome_email.body.count(upload_photo_url))
        
        # rewind and this add a profile photo
        WelcomeEmail.objects.all().delete()
        person.photo = 'photo.jpg'
        person.save()
        response = self.client.get('/welcome/create-welcome-emails/')
        self.assertEqual(response.status_code, 200)
        # if the user signed up a long time ago no welcome email should be
        # sent
        self.assertEqual(response.content, 'Created 1 welcome email')
        welcome_email = WelcomeEmail.objects.get(user=user)
        edit_style_url = reverse('edit_style', args=('bob',))
        self.assertTrue(welcome_email.body.count(edit_style_url))

        # rewind and this add a style
        WelcomeEmail.objects.all().delete()
        style = Style.objects.create(name=u'Fat Style')
        person.styles.add(style)
        person.save()
        response = self.client.get('/welcome/create-welcome-emails/')
        self.assertEqual(response.status_code, 200)
        # if the user signed up a long time ago no welcome email should be
        # sent
        self.assertEqual(response.content, 'Created 1 welcome email')
        welcome_email = WelcomeEmail.objects.get(user=user)
        edit_club_url = reverse('edit_club', args=('bob',))
        self.assertTrue(welcome_email.body.count(edit_club_url))
        
        # rewind and this add a club
        WelcomeEmail.objects.all().delete()
        club = Club.objects.create(name=u'My club', url='http://www.com')
        person.club_membership.add(club)
        person.save()
        response = self.client.get('/welcome/create-welcome-emails/')
        self.assertEqual(response.status_code, 200)
        # if the user signed up a long time ago no welcome email should be
        # sent
        self.assertEqual(response.content, 'Created 1 welcome email')
        welcome_email = WelcomeEmail.objects.get(user=user)
        edit_profile_url = reverse('edit_profile', args=('bob',))
        self.assertTrue(welcome_email.body.count(edit_profile_url))
        
        # rewind and this add a bio
        WelcomeEmail.objects.all().delete()
        person.bio = u"I love fish"
        person.save()
        response = self.client.get('/welcome/create-welcome-emails/')
        self.assertEqual(response.status_code, 200)
        # if the user signed up a long time ago no welcome email should be
        # sent
        self.assertEqual(response.content, 'Created 1 welcome email')
        welcome_email = WelcomeEmail.objects.get(user=user)
        edit_profile_url = reverse('edit_profile', args=('bob',))
        self.assertTrue(not welcome_email.body.count(edit_profile_url))
        
        # Now actually send it
        WelcomeEmail.objects.all().delete()
        response = self.client.get('/welcome/create-welcome-emails/')
        self.assertEqual(response.status_code, 200)
        # if the user signed up a long time ago no welcome email should be
        # sent
        self.assertEqual(response.content, 'Created 1 welcome email')
        self.assertEqual(WelcomeEmail.objects.count(), 1)
        
        response = self.client.get('/welcome/send-unsent-emails/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Sent 1 email')
        
        self.assertEqual(len(mail.outbox), 1)
        email_sent = mail.outbox[0]
        self.assertEqual(email_sent.from_email, settings.WELCOME_EMAIL_SENDER)
        self.assertTrue(u'bob@example.com' in email_sent.recipients())
        self.assertTrue(settings.PROJECT_NAME in email_sent.subject)

        # rewind and test the combined create-and-send-unsent-emails view
        WelcomeEmail.objects.all().delete()
        response = self.client.get('/welcome/create-and-send-unsent-emails/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'Sent 1 email')
        
        # Run it again
        response = self.client.get('/welcome/create-and-send-unsent-emails/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'No welcome emails this time')
        