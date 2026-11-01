
from datetime import timedelta
import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import PhoneOTP, User


OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_REQUESTS_PER_HOUR = 5


class OTPRequestLimitError(Exception):
    pass


def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


@transaction.atomic
def create_phone_otp(user):
    # Lock the user row to serialize simultaneous OTP requests.
    locked_user = User.objects.select_for_update().get(pk=user.pk)

    now = timezone.now()

    latest_otp = PhoneOTP.objects.filter(
        user=locked_user
    ).order_by("-created_at").first()

    if latest_otp:
        elapsed = (now - latest_otp.created_at).total_seconds()

        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            raise OTPRequestLimitError(
                "Please wait before requesting another OTP."
            )

    one_hour_ago = now - timedelta(hours=1)

    recent_requests = PhoneOTP.objects.filter(
        user=locked_user,
        created_at__gte=one_hour_ago
    ).count()

    if recent_requests >= OTP_MAX_REQUESTS_PER_HOUR:
        raise OTPRequestLimitError(
            "OTP request limit reached. Please try again later."
        )

    PhoneOTP.objects.filter(
        user=locked_user,
        is_used=False
    ).update(is_used=True)

    otp = generate_otp()

    PhoneOTP.objects.create(
        user=locked_user,
        otp_hash=make_password(otp),
        expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES)
    )

    return otp


@transaction.atomic
def verify_phone_otp(user, submitted_otp):
    otp_record = PhoneOTP.objects.select_for_update().filter(
        user=user,
        is_used=False
    ).order_by("-created_at").first()

    if otp_record is None:
        return False, "No active OTP found."

    now = timezone.now()

    if otp_record.expires_at <= now:
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])
        return False, "OTP has expired."

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])
        return False, "Maximum OTP attempts exceeded."

    otp_record.attempts += 1

    if not check_password(submitted_otp, otp_record.otp_hash):
        if otp_record.attempts >= OTP_MAX_ATTEMPTS:
            otp_record.is_used = True

        otp_record.save(update_fields=["attempts", "is_used"])
        return False, "Invalid OTP."

    otp_record.is_used = True
    otp_record.save(update_fields=["is_used"])

    return True, "Phone number verified successfully."


@transaction.atomic
def invalidate_active_phone_otps(user):
    PhoneOTP.objects.filter(user=user, is_used=False).update(is_used=True)
