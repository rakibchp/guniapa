from django.utils import timezone
from rest_framework import serializers

from apps.marketplace.models import (
    Booking,
    BookingStatusHistory,
    CashPayment,
    Notification,
    ProviderSkill,
    Review,
    ServiceCategory,
    ServiceOffer,
    ServiceRequest,
    SupportTicket,
)


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ["id", "name", "slug", "description", "requires_credential"]
        read_only_fields = fields


class ProviderSkillSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = ProviderSkill
        fields = [
            "id",
            "category",
            "category_name",
            "experience_years",
            "description",
            "approval_status",
            "credential_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "category_name",
            "approval_status",
            "credential_verified",
            "created_at",
            "updated_at",
        ]

    def validate_category(self, category):
        if not category.is_active:
            raise serializers.ValidationError("This service category is unavailable.")
        return category


class ServiceRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "category",
            "details",
            "service_city",
            "service_address",
            "requested_for",
            "pricing_model",
            "proposed_amount",
            "duration_hours",
            "currency",
            "status",
            "created_at",
        ]
        read_only_fields = ["id", "currency", "status", "created_at"]

    def validate_category(self, category):
        if not category.is_active:
            raise serializers.ValidationError("This service category is unavailable.")
        return category

    def validate_requested_for(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Choose a future service date and time.")
        return value

    def validate(self, attrs):
        pricing_model = attrs.get("pricing_model")
        amount = attrs.get("proposed_amount")
        duration = attrs.get("duration_hours")
        if pricing_model == ServiceRequest.PricingModel.FIXED:
            if amount is None or amount <= 0:
                raise serializers.ValidationError(
                    {"proposed_amount": "Enter a fixed price greater than zero."}
                )
            if duration is not None:
                raise serializers.ValidationError(
                    {"duration_hours": "Duration is only used for hourly pricing."}
                )
        elif pricing_model == ServiceRequest.PricingModel.HOURLY:
            if amount is None or amount <= 0:
                raise serializers.ValidationError(
                    {"proposed_amount": "Enter an hourly rate greater than zero."}
                )
            if duration is None or duration <= 0:
                raise serializers.ValidationError(
                    {"duration_hours": "Enter an estimated duration greater than zero."}
                )
        elif duration is not None:
            raise serializers.ValidationError(
                {"duration_hours": "Duration is only used for hourly pricing."}
            )
        return attrs


class AvailableServiceRequestSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = ServiceRequest
        fields = [
            "id",
            "category",
            "category_name",
            "details",
            "service_city",
            "requested_for",
            "pricing_model",
            "proposed_amount",
            "duration_hours",
            "currency",
            "created_at",
        ]
        read_only_fields = fields


class ServiceOfferCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceOffer
        fields = ["amount", "message"]

    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError("Enter a quote greater than zero.")
        return amount


class ServiceOfferSerializer(serializers.ModelSerializer):
    provider_id = serializers.UUIDField(source="provider.id", read_only=True)
    provider_name = serializers.CharField(source="provider.user.full_name", read_only=True)
    professional_title = serializers.CharField(
        source="provider.professional_title",
        read_only=True,
    )

    class Meta:
        model = ServiceOffer
        fields = [
            "id",
            "provider_id",
            "provider_name",
            "professional_title",
            "amount",
            "message",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True)

    class Meta:
        model = BookingStatusHistory
        fields = ["from_status", "to_status", "actor_name", "created_at"]
        read_only_fields = fields


class BookingSerializer(serializers.ModelSerializer):
    request_id = serializers.UUIDField(source="service_request.id", read_only=True)
    category_id = serializers.UUIDField(
        source="service_request.category.id",
        read_only=True,
    )
    category_name = serializers.CharField(
        source="service_request.category.name",
        read_only=True,
    )
    details = serializers.CharField(source="service_request.details", read_only=True)
    service_city = serializers.CharField(
        source="service_request.service_city",
        read_only=True,
    )
    service_address = serializers.CharField(
        source="service_request.service_address",
        read_only=True,
    )
    requested_for = serializers.DateTimeField(
        source="service_request.requested_for",
        read_only=True,
    )
    pricing_model = serializers.CharField(
        source="service_request.pricing_model",
        read_only=True,
    )
    proposed_amount = serializers.DecimalField(
        source="service_request.proposed_amount",
        max_digits=10,
        decimal_places=2,
        allow_null=True,
        read_only=True,
    )
    duration_hours = serializers.DecimalField(
        source="service_request.duration_hours",
        max_digits=5,
        decimal_places=2,
        allow_null=True,
        read_only=True,
    )
    customer_name = serializers.CharField(
        source="service_request.customer.full_name",
        read_only=True,
    )
    provider_name = serializers.CharField(
        source="provider.user.full_name",
        read_only=True,
    )
    status_history = BookingStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "request_id",
            "category_id",
            "category_name",
            "customer_name",
            "provider_name",
            "details",
            "service_city",
            "service_address",
            "requested_for",
            "pricing_model",
            "proposed_amount",
            "duration_hours",
            "agreed_amount",
            "customer_fee",
            "provider_fee",
            "currency",
            "status",
            "created_at",
            "updated_at",
            "completed_at",
            "status_history",
        ]
        read_only_fields = fields


class BookingTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Booking.Status.choices)


class CashPaymentSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(
        source="recorded_by.full_name",
        read_only=True,
    )

    class Meta:
        model = CashPayment
        fields = [
            "id",
            "amount",
            "currency",
            "recorded_by_name",
            "received_at",
        ]
        read_only_fields = fields


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["rating", "comment"]


class PublicReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.full_name", read_only=True)

    class Meta:
        model = Review
        fields = ["rating", "comment", "customer_name", "created_at"]
        read_only_fields = fields


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ["id", "booking", "subject", "description", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]

    def validate_booking(self, booking):
        user = self.context["request"].user
        if (
            booking.service_request.customer_id != user.id
            and booking.provider.user_id != user.id
        ):
            raise serializers.ValidationError("This booking is unavailable.")
        return booking


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = [
            "id",
            "booking",
            "subject",
            "description",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "kind",
            "message",
            "booking",
            "service_request",
            "is_read",
            "created_at",
        ]
        read_only_fields = fields
