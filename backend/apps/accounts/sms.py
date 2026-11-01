import logging
from typing import Protocol

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class SMSDeliveryError(Exception):
    """Raised when an OTP cannot be handed to the configured SMS provider."""


class SMSProvider(Protocol):
    def send(self, phone_number: str, message: str) -> None: ...


def deliver_phone_otp(phone_number: str, otp: str) -> None:
    if settings.DEBUG and getattr(settings, "SMS_BACKEND", "console") == "console":
        return

    adapter_path = getattr(settings, "SMS_PROVIDER_ADAPTER", "")
    if not adapter_path:
        raise ImproperlyConfigured(
            "Configure SMS_PROVIDER_ADAPTER before enabling phone OTP outside development."
        )

    try:
        adapter_class = import_string(adapter_path)
    except (ImportError, AttributeError) as error:
        logger.exception("Configured SMS provider adapter could not be loaded.")
        raise ImproperlyConfigured(
            "Configured SMS_PROVIDER_ADAPTER could not be loaded."
        ) from error

    adapter: SMSProvider = adapter_class()
    try:
        adapter.send(
            phone_number,
            f"Your Guniapa verification code is {otp}. It expires in 5 minutes.",
        )
    except SMSDeliveryError:
        logger.exception("SMS provider failed to deliver a phone verification code.")
        raise
