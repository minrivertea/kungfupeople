from testbase import TestCase

from djangopeople import utils

class UtilsTestCase(TestCase):
    
    def setUp(self):
        super(UtilsTestCase, self).setUp()
        
    def tearDown(self):
        super(UtilsTestCase, self).tearDown()
    
    def test_get_previous_next(self):
        """should work with any iterable"""
        func = utils.get_previous_next
        
        prev_next = func(list('ABC'), 'B')
        self.assertTrue(type(prev_next) is tuple)
        self.assertEqual(len(prev_next), 2)
        previous, next = prev_next
        self.assertEqual(previous, 'A')
        self.assertEqual(next, 'C')
        
        previous, next = func(list('ABC'), 'A')
        self.assertEqual(previous, None)
        self.assertEqual(next, 'B')
        
        previous, next = func(list('ABC'), 'C')
        self.assertEqual(previous, 'B')
        self.assertEqual(next, None)
        
        previous, next = func(list('ABC'), 'D')
        self.assertEqual(previous, None)
        self.assertEqual(next, None)
        
    def test_prowlpy_wrapper(self):
        if not utils.prowl_api:
            return
        func = utils.prowlpy_wrapper
        
        event = "Kung fu person created"
        description = u'Muhammed G\xfcm\xfc\u015f just joined!!!'
        
        # priority is supposed to be a number
        self.assertRaises(ValueError, func, event, description, priority='top')
        # must be >= -2 and <= 2
        self.assertRaises(AssertionError, func, event, description, priority=-3)
        self.assertRaises(AssertionError, func, event, description, priority=3)
        
        func(event, description=description)
        # this should have posted a prowl
        posted_prowls = self._get_posted_prowls()
        count_posted_prowls = len(posted_prowls)
        self.assertTrue(count_posted_prowls > 0)
        latest_posted_prowl = posted_prowls[-1]
        
        # you can call the function twice but it's caught by cache
        # to prevent accidentally posting twice
        func(event, description=description)
        posted_prowls = self._get_posted_prowls()
        self.assertEqual(len(posted_prowls), count_posted_prowls)

        
        
        
        
        
        
        
