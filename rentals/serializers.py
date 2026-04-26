from rest_framework import serializers
from .models import Villa, Booking, Review


class VillaSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Villa
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.main_image:
            return request.build_absolute_uri(obj.main_image.url)
        return None


class BookingSerializer(serializers.ModelSerializer):
    villa_id = serializers.PrimaryKeyRelatedField(
        queryset=Villa.objects.all(),
        source='villa'
    )

    class Meta:
        model = Booking
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'