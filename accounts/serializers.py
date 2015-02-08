from rest_framework import serializers
from accounts.models import User


class AppointmentItemSerializer(serializers.Serializer):
    treatment = serializers.CharField(max_length=200, source='treatment.booker_id')
    employee_name = serializers.CharField(max_length=200)


class AppointmentSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=200)
    start_datetime = serializers.DateTimeField()
    can_cancel = serializers.BooleanField()
    final_total = serializers.DecimalField(max_digits=10, decimal_places=2)
    treatments = AppointmentItemSerializer(many=True)

class UserSerializer(serializers.ModelSerializer):
    appointments = AppointmentSerializer(many=True)

    class Meta:
        fields = ('booker_id', 'first_name', 'last_name', 'id', 'phone_number', 'photo', 'email', 'appointments')
        model = User


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=200)


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('first_name', 'last_name', 'phone_number', 'email', 'password')
        model = User

    def create(self, validated_data):
        user = User()
        user.set_password(validated_data["password"])
        user.email = validated_data['email']
        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.phone_number = validated_data['phone_number']
        return user
