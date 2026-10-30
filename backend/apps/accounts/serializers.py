
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.accounts.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "phone_number",
            "password",
            "role",
        ]
        read_only_fields = ["id"]

    def validate_email(self, value):
        value = value.strip().lower()

        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )

        return value

    def validate_phone_number(self, value):
        value = value.strip()

        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                "An account with this phone number already exists."
            )

        return value

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError(
                "Administrator accounts cannot be registered publicly."
            )

        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        return User.objects.create_user(
            password=password,
            **validated_data
        )


class UserLoginSerializer(serializers.Serializer):

    identifier = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )



class SendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=16)


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=16)

    otp = serializers.RegexField(
        regex=r"^\d{6}$",
        error_messages={
            "invalid": "OTP must contain exactly 6 digits."
        }
    )
