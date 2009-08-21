from testbase import TestCase

from djangopeople import utils

class UtilsTestCase(TestCase):
    
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
        
        
        
        
        
        
        
        
