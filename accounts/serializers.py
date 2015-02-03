from rest_framework import serializers
from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('booker_id', 'first_name', 'last_name', 'id', 'phone_number', 'photo', 'email')
        model = User


class ForgotPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('email', 'first_name')
        model = User


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
