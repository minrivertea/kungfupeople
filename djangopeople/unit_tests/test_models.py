from django.conf import settings
from testbase import TestCase

from djangopeople.models import KungfuPerson, Country

class ModelsTestCase(TestCase):
    
    def test_get_nearest(self):
        """test KungfuPerson.get_nearest()
        
        It should return KungfuPerson instances in order by distance
        and not those that are too far away.
        """
        switzerland = Country.objects.get(name=u"Switzerland")
        uk = Country.objects.get(name=u"United Kingdom")
        
        user1, person1 = self._create_person("user1", "user1@example.com",
                                             country=switzerland.name,
                                             latitude=46.519582,
                                             longitude=6.632121,
                                             location_description=u"Geneva")
        # Geneva -> Saint-Genis: 10.9km
        user2, person2 = self._create_person("user2", "user2@example.com",
                                             country=switzerland.name,
                                             latitude=46.205973,
                                             longitude=6.5995789,
                                             location_description=u"Saint-Genis")
                
        # Geneva -> Islington: 986km
        user3, person3 = self._create_person("user3", "user3@example.com",
                                             country=uk.name,
                                             latitude=51.532601866,
                                             longitude=-0.108382701874,
                                             location_description=u"Islington")
        
        # Geneva -> Lausanne: 63.2km
        user4, person4 = self._create_person("user4", "user4@example.com",
                                             country=switzerland.name,
                                             latitude=46.243572,
                                             longitude=6.02107,
                                             location_description=u"Lausanne")
        
        
        near = person1.get_nearest(within_range=9999)
        
        self.assertEqual(near, [person2, person4, person3])
        
        # the within range feature doesn't work in mysql
        if settings.DATABASE_ENGINE == 'mysql':
            return
        
        # person2: 21.7 miles
        # person4: 34.7 miles
        # person3: 471.9 miles
        near = person1.get_nearest(within_range=100)
        
        self.assertEqual(near, [person2, person4])
        
        near = person1.get_nearest(num=1, within_range=100)
        
        self.assertEqual(near, [person2])
        
        
        