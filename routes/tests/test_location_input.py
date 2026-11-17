"""Compatibility checks for city/state text input without geocoding calls."""
from django.test import SimpleTestCase

from routes.serializers import RouteSerializer


class LocationInputTests(SimpleTestCase):
    def test_compact_city_state_and_structured_locations_normalize_identically(self):
        compact = RouteSerializer(data={
            'start': ' Chicago, il ',
            'finish': 'Denver, CO',
        })
        structured = RouteSerializer(data={
            'start': {'city': 'Chicago', 'state': 'IL'},
            'finish': {'city': 'Denver', 'state': 'CO'},
        })
        self.assertTrue(compact.is_valid(), compact.errors)
        self.assertTrue(structured.is_valid(), structured.errors)
        self.assertEqual(compact.validated_data, structured.validated_data)

    def test_mixed_formats_remain_valid(self):
        serializer = RouteSerializer(data={
            'start': 'Washington, DC',
            'finish': {'city': 'Baltimore', 'state': 'MD'},
        })
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['start'],
                         {'city': 'Washington', 'state': 'DC'})

    def test_invalid_or_ambiguous_strings_are_rejected(self):
        for value in ('Chicago', 'Chicago, Illinois', ', IL',
                      'Chicago, ZZ, USA', 'Chicago, 12'):
            with self.subTest(value=value):
                serializer = RouteSerializer(data={
                    'start': value, 'finish': 'Denver, CO',
                })
                self.assertFalse(serializer.is_valid())
                self.assertIn('start', serializer.errors)

    def test_existing_object_contract_stays_required(self):
        serializer = RouteSerializer(data={
            'start': {'city': 'Chicago', 'state': 'IL'},
            'finish': {'city': 'Denver'},
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('finish', serializer.errors)
