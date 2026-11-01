
from rest_framework import serializers

from apps.accounts.models import ProviderProfile


class ProviderProfileSerializer(serializers.ModelSerializer):

    user_id = serializers.UUIDField(
        source="user.id",
        read_only=True
    )

    class Meta:
        model = ProviderProfile

        fields = [
            "id",
            "user_id",
            "professional_title",
            "bio",
            "experience_years",
            "city",
            "service_area",
            "service_radius_km",
            "approval_status",
            "is_available",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "user_id",
            "approval_status",
            "created_at",
            "updated_at",
        ]

    def validate_experience_years(self, value):
        if value > 60:
            raise serializers.ValidationError(
                "Experience years cannot exceed 60."
            )
        return value

    def validate_service_radius_km(self, value):
        if value < 1 or value > 100:
            raise serializers.ValidationError(
                "Service radius must be between 1 and 100 km."
            )
        return value


class PublicProviderSerializer(serializers.ModelSerializer):

    provider_name = serializers.CharField(
        source="user.full_name",
        read_only=True
    )

    class Meta:
        model = ProviderProfile

        fields = [
            "id",
            "provider_name",
            "professional_title",
            "bio",
            "experience_years",
            "city",
            "is_available",
        ]
