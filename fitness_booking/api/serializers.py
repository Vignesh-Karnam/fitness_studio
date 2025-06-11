from django.utils.timezone import localtime
from rest_framework import serializers

from .models import Booking, FitnessClass


class FitnessClassSerializer(serializers.ModelSerializer):
    datetime_ist = serializers.SerializerMethodField()

    class Meta:
        model = FitnessClass
        fields = ['id', 'name', 'instructor', 'datetime', 'datetime_ist', 'available_slots']

    def get_datetime_ist(self, obj):
        return localtime(obj.datetime).strftime('%Y-%m-%d %H:%M:%S')


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['fitness_class', 'client_name', 'client_email']

    def validate_client_email(self, value):
        if not value or '@' not in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value

    def validate_client_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Client name cannot be blank.")
        return value
