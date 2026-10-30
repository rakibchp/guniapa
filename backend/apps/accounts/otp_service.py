
import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import PhoneOTP


OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 5


def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


def hash_otp(otp):
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def create_phone_otp(user):
    now = timezone.now()

    # Invalidate previous unused OTPs.
    PhoneOTP.objects.filter(
        user=user,
        is_used=False
    ).update(is_used=True)

    otp = generate_otp()

    PhoneOTP.objects.create(
        user=user,
        otp_hash=hash_otp(otp),
        expires_at=now + timedelta(minutes=OTP_EXPIRY_MINUTES)
    )

    return otp


def verify_phone_otp(user, submitted_otp):
    otp_record = PhoneOTP.objects.filter(
        user=user,
        is_used=False
    ).order_by("-created_at").first()

    if otp_record is None:
        return False, "No active OTP found."

    if otp_record.expires_at <= timezone.now():
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])
        return False, "OTP has expired."

    if otp_record.attempts >= OTP_MAX_ATTEMPTS:
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])
        return False, "Maximum OTP attempts exceeded."

    otp_record.attempts += 1

    if not secrets.compare_digest(
        otp_record.otp_hash,
        hash_otp(submitted_otp)
    ):
        if otp_record.attempts >= OTP_MAX_ATTEMPTS:
            otp_record.is_used = True

        otp_record.save(update_fields=["attempts", "is_used"])
        return False, "Invalid OTP."

    otp_record.is_used = True
    otp_record.save(update_fields=["is_used"])

    return True, "Phone number verified successfully."
