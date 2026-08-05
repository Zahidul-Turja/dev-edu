from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from user_management.models import User, SocialLink


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
    otp = serializers.CharField(max_length=4, min_length=4)


class SocialLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialLink
        fields = ["platform", "url"]


class UserOwnProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    social_links = SocialLinkSerializer(many=True)

    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "role",
            "avatar",
            "about",
            "gender",
            "date_of_birth",
            "social_links",
        ]

    def get_avatar(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.get_avatar())
