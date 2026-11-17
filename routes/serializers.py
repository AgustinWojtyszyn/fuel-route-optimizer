from rest_framework import serializers
class PlaceSerializer(serializers.Serializer):
    city = serializers.CharField(max_length=160, trim_whitespace=True)
    state = serializers.RegexField(r'^[A-Za-z]{2}$')
    def validate(self, attrs):
        attrs['state'] = attrs['state'].upper()
        return attrs
class RouteSerializer(serializers.Serializer):
    start = PlaceSerializer()
    finish = PlaceSerializer()

    def to_internal_value(self, data):
        # Accept either structured {"city": ..., "state": ...} locations or
        # the conventional "City, ST" shorthand. Both paths resolve through
        # the same local gazetteer without consuming geocoding API calls.
        if isinstance(data, dict):
            data = dict(data)
            for field in ('start', 'finish'):
                value = data.get(field)
                if isinstance(value, str) and ',' in value:
                    city, state = value.rsplit(',', 1)
                    data[field] = {'city': city.strip(), 'state': state.strip()}
        return super().to_internal_value(data)
