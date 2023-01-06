from django.test import TestCase

from .models import Location, Participant

class LocationTests(TestCase):
    def test_add_loc(self):
        loc = Location(\
        city='San Mateo',\
        state='CA',\
        country='United States'\
        )
        out_str = '{}, {}, {}'.format(loc.city, loc.state, loc.country)

        self.assertEqual(out_str,\
        'San Mateo, CA, United States')
