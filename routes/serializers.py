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
