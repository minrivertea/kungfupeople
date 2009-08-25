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
        
        
        near = person1.get_nearest()
        
        self.assertEqual(near, [person2, person4, person3])
        
        from geopy import distance as geopy_distance
        def distance((latitude1, longitude1), (latitude2, longitude2)):
            print "select miles_between_lat_long(%s, %s, %s, %s);"%(latitude1, longitude1, latitude2, longitude2)
            return geopy_distance.distance((latitude1, longitude1), 
                                           (latitude2, longitude2)).miles
        start = (person1.latitude, person1.longitude)
        saint_genis = (person2.latitude, person2.longitude)
        islington = (person3.latitude, person3.longitude)
        lausanne = (person4.latitude, person4.longitude)
        print distance(start, saint_genis)
        print distance(start, islington)
        print distance(start, lausanne)
        
        print near
        
        