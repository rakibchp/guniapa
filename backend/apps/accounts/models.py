from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils import timezone
from apps.accounts.managers import UserManager
from django.conf import settings
# Create your models here.



class User(AbstractBaseUser, PermissionsMixin):

    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        PROVIDER = "PROVIDER", "Service Provider"
        ADMIN = "ADMIN", "Administrator"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    full_name = models.CharField(max_length=150)

    email = models.EmailField(
        unique=True,
        db_index=True
    )

    phone_number = models.CharField(
        max_length=16,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^\+?[1-9]\d{7,14}$",
                message="Enter a valid international phone number."
            )
        ]
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number", "full_name"]

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email



class PhoneOTP(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="phone_otps"
    )

    otp_hash = models.CharField(max_length=128)

    expires_at = models.DateTimeField()

    is_used = models.BooleanField(default=False)

    attempts = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "phone_otps"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_used"]),
        ]

    def __str__(self):
        return f"Phone OTP for {self.user.email}"



class ProviderProfile(models.Model):

    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        SUSPENDED = "SUSPENDED", "Suspended"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_profile"
    )

    professional_title = models.CharField(
        max_length=150,
        blank=True
    )

    bio = models.TextField(
        blank=True,
        max_length=1000
    )

    experience_years = models.PositiveSmallIntegerField(
        default=0
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    service_area = models.CharField(
        max_length=255,
        blank=True
    )

    service_radius_km = models.PositiveSmallIntegerField(
        default=5
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING
    )

    is_available = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "provider_profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Provider Profile - {self.user.email}"
