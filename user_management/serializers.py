from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from user_management.models import User


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "full_name",
            "gender",
            "date_of_birth",
        ]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EmailOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)
