from rest_framework import serializers
from booking.models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        # fields = ('booker_id', 'first_name', 'last_name', 'id', 'phone_number', 'photo', 'email')
        model = Appointment


class BookingSerializer(serializers.Serializer):
    time = serializers.DateTimeField()
    booker_id = serializers.CharField()
    name_on_card = serializers.CharField()
    card_number = serializers.CharField()
    expiry_month = serializers.IntegerField()
    expiry_year = serializers.IntegerField()
    card_code = serializers.CharField()
    billing_zip_code = serializers.CharField()
    street_address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    zip_code = serializers.CharField()


class StylistListSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()
    ID = serializers.IntegerField()

    def get_name(self, obj):
        return obj['FirstName']