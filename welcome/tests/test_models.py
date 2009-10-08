# python
import datetime

# django
from django.core import mail

from djangopeople.unit_tests.testbase import TestCase
from welcome.models import WelcomeEmail

class ModelTestCase(TestCase):
    
    def test_basic_creation(self):
        user, person = self._create_person('bob', 'bob@example.com')
        welcome_email = WelcomeEmail.objects.create(user=user,
                                                    subject='Test',
                                                    body='Test body')
        self.assertEqual(welcome_email.email, 'bob@example.com')
        self.assertEqual(welcome_email.send_date, None)
        welcome_email.send()
        
        welcome_email = WelcomeEmail.objects.get(user=user)
        self.assertNotEqual(welcome_email.send_date, None)
        self.assertTrue(welcome_email.send_date <= datetime.datetime.now())
        
        
