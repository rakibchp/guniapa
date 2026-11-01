import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import ProviderProfile


class ServiceCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, max_length=1000)
    region_code = models.CharField(max_length=3, default="BD")
    requires_credential = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "service categories"
        indexes = [models.Index(fields=["is_active", "region_code"])]

    def __str__(self):
        return self.name


class ProviderSkill(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="provider_skills",
    )
    experience_years = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(60)],
    )
    description = models.CharField(max_length=500, blank=True)
    approval_status = models.CharField(
        max_length=12,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    credential_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "category"],
                name="unique_provider_service_category",
            ),
        ]
        indexes = [models.Index(fields=["category", "approval_status"])]

    def __str__(self):
        return f"{self.provider_id}: {self.category}"


class FeeRule(models.Model):
    version = models.PositiveIntegerField(unique=True)
    customer_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    provider_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="BDT")
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_fee_rules",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [
            models.CheckConstraint(
                condition=Q(customer_fee__gte=0) & Q(provider_fee__gte=0),
                name="fee_rule_amounts_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(currency="BDT"),
                name="fee_rule_currency_bdt",
            ),
        ]

    def __str__(self):
        return f"Fee rule v{self.version}"


class ServiceRequest(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ACCEPTED = "ACCEPTED", "Accepted"
        CANCELLED = "CANCELLED", "Cancelled"
        EXPIRED = "EXPIRED", "Expired"

    class PricingModel(models.TextChoices):
        FIXED = "FIXED", "Fixed price"
        HOURLY = "HOURLY", "Hourly"
        QUOTE = "QUOTE", "Provider quote"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="service_requests",
    )
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name="service_requests",
    )
    details = models.TextField(max_length=2000)
    service_city = models.CharField(max_length=100)
    service_address = models.CharField(max_length=500)
    requested_for = models.DateTimeField()
    pricing_model = models.CharField(
        max_length=8,
        choices=PricingModel.choices,
    )
    proposed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    duration_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="BDT")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "category", "service_city"]),
            models.Index(fields=["customer", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(currency="BDT"),
                name="service_request_currency_bdt",
            ),
            models.CheckConstraint(
                condition=Q(proposed_amount__isnull=True)
                | Q(proposed_amount__gte=0),
                name="service_request_amount_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(duration_hours__isnull=True)
                | Q(duration_hours__gt=0),
                name="service_request_duration_positive",
            ),
        ]

    def __str__(self):
        return f"{self.category} request {self.id}"


class ServiceOffer(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending customer decision"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"
        REVOKED = "REVOKED", "Revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.PROTECT,
        related_name="offers",
    )
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.PROTECT,
        related_name="service_offers",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    message = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["amount", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["service_request", "provider"],
                name="unique_provider_offer_per_request",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="service_offer_amount_positive",
            ),
        ]


class Booking(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Accepted"
        ARRIVING = "ARRIVING", "Provider arriving"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETION_PENDING = "COMPLETION_PENDING", "Completion pending"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"
        DISPUTED = "DISPUTED", "Disputed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_request = models.OneToOneField(
        ServiceRequest,
        on_delete=models.PROTECT,
        related_name="booking",
    )
    service_offer = models.OneToOneField(
        ServiceOffer,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="booking",
    )
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACCEPTED,
    )
    agreed_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    customer_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    provider_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    fee_rule = models.ForeignKey(
        FeeRule,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="bookings",
    )
    currency = models.CharField(max_length=3, default="BDT")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["provider", "status", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(agreed_amount__gt=0),
                name="booking_agreed_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(customer_fee__gte=0) & Q(provider_fee__gte=0),
                name="booking_fees_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(currency="BDT"),
                name="booking_currency_bdt",
            ),
        ]

    def __str__(self):
        return f"Booking {self.id} ({self.status})"


class BookingStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name="status_history",
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, choices=Booking.Status.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="booking_status_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["booking", "created_at"])]


class FeeLedgerEntry(models.Model):
    class Party(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        PROVIDER = "PROVIDER", "Provider"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        related_name="fee_entries",
    )
    party = models.CharField(max_length=8, choices=Party.choices)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="BDT")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["booking", "party"],
                name="unique_booking_fee_party",
            ),
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="fee_entry_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(currency="BDT"),
                name="fee_entry_currency_bdt",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and FeeLedgerEntry.objects.filter(pk=self.pk).exists():
            raise ValueError("Fee ledger entries are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Fee ledger entries are append-only.")


class CashPayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        Booking,
        on_delete=models.PROTECT,
        related_name="cash_payment",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cash_payments_recorded",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(max_length=3, default="BDT")
    received_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="cash_payment_amount_positive",
            ),
            models.CheckConstraint(
                condition=Q(currency="BDT"),
                name="cash_payment_currency_bdt",
            ),
        ]


class Review(models.Model):
    class ModerationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PUBLISHED = "PUBLISHED", "Published"
        HIDDEN = "HIDDEN", "Hidden"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.OneToOneField(
        Booking,
        on_delete=models.PROTECT,
        related_name="review",
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviews_written",
    )
    provider = models.ForeignKey(
        ProviderProfile,
        on_delete=models.PROTECT,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.CharField(max_length=1000, blank=True)
    moderation_status = models.CharField(
        max_length=10,
        choices=ModerationStatus.choices,
        default=ModerationStatus.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["provider", "moderation_status"])]
        constraints = [
            models.CheckConstraint(
                condition=Q(rating__gte=1) & Q(rating__lte=5),
                name="review_rating_between_one_and_five",
            ),
        ]


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_REVIEW = "IN_REVIEW", "In review"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="support_tickets",
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="support_tickets",
    )
    subject = models.CharField(max_length=160)
    description = models.TextField(max_length=3000)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.OPEN,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_support_tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["opened_by", "created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]


class Notification(models.Model):
    class Kind(models.TextChoices):
        BOOKING_UPDATE = "BOOKING_UPDATE", "Booking update"
        SERVICE_OFFER = "SERVICE_OFFER", "Service offer"
        SUPPORT_UPDATE = "SUPPORT_UPDATE", "Support update"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="marketplace_notifications",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    message = models.CharField(max_length=250)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "is_read", "created_at"])]


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="marketplace_audit_events",
    )
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=80)
    target_id = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_type", "target_id", "created_at"])]

    def save(self, *args, **kwargs):
        if self.pk and AuditEvent.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit events are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Audit events are append-only.")
