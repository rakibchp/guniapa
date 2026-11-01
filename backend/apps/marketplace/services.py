from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError

from apps.accounts.models import ProviderProfile, User
from apps.marketplace.models import (
    AuditEvent,
    Booking,
    BookingStatusHistory,
    CashPayment,
    FeeLedgerEntry,
    FeeRule,
    Notification,
    ProviderSkill,
    Review,
    ServiceOffer,
    ServiceRequest,
)


class Conflict(APIException):
    status_code = 409
    default_detail = "This item has changed. Refresh and try again."
    default_code = "conflict"


def _provider_profile(actor):
    if (
        actor.role != User.Role.PROVIDER
        or not actor.is_active
        or not actor.is_phone_verified
    ):
        raise PermissionDenied("A verified provider account is required.")
    try:
        profile = ProviderProfile.objects.get(user=actor)
    except ProviderProfile.DoesNotExist as error:
        raise PermissionDenied("Complete your provider profile first.") from error
    if (
        profile.approval_status != ProviderProfile.ApprovalStatus.APPROVED
        or not profile.is_available
    ):
        raise PermissionDenied("Your provider profile is not approved and available.")
    return profile


def _ensure_provider_eligible(profile, service_request):
    skill = ProviderSkill.objects.filter(
        provider=profile,
        category=service_request.category,
        approval_status=ProviderSkill.ApprovalStatus.APPROVED,
    ).first()
    if skill is None:
        raise PermissionDenied("An approved skill for this service is required.")
    if service_request.category.requires_credential and not skill.credential_verified:
        raise PermissionDenied(
            "The required credential for this service has not been verified."
        )


def _current_fee_rule():
    return FeeRule.objects.filter(is_active=True).order_by("-version").first()


def _fee_values(rule):
    if rule is None:
        return None, Decimal("0.00"), Decimal("0.00")
    return rule, rule.customer_fee, rule.provider_fee


def _notify(user, kind, message, booking=None, service_request=None):
    Notification.objects.create(
        recipient=user,
        kind=kind,
        message=message,
        booking=booking,
        service_request=service_request,
    )


def _audit(actor, action, target):
    AuditEvent.objects.create(
        actor=actor,
        action=action,
        target_type=target.__class__.__name__,
        target_id=str(target.pk),
    )


def _booking_for_fixed_price(service_request):
    if service_request.pricing_model == ServiceRequest.PricingModel.FIXED:
        return service_request.proposed_amount
    if service_request.pricing_model == ServiceRequest.PricingModel.HOURLY:
        amount = service_request.proposed_amount * service_request.duration_hours
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    raise ValidationError(
        {"pricing_model": "Quote-based requests must be accepted through an offer."}
    )


@transaction.atomic
def accept_fixed_price_request(request_id, actor):
    service_request = (
        ServiceRequest.objects.select_for_update()
        .select_related("customer", "category")
        .filter(pk=request_id)
        .first()
    )
    if service_request is None:
        raise ServiceRequest.DoesNotExist
    if service_request.status != ServiceRequest.Status.OPEN:
        raise Conflict("This request is no longer available.")
    profile = _provider_profile(actor)
    _ensure_provider_eligible(profile, service_request)
    amount = _booking_for_fixed_price(service_request)
    fee_rule, customer_fee, provider_fee = _fee_values(_current_fee_rule())

    booking = Booking.objects.create(
        service_request=service_request,
        provider=profile,
        agreed_amount=amount,
        fee_rule=fee_rule,
        customer_fee=customer_fee,
        provider_fee=provider_fee,
    )
    service_request.status = ServiceRequest.Status.ACCEPTED
    service_request.save(update_fields=["status", "updated_at"])
    BookingStatusHistory.objects.create(
        booking=booking,
        from_status="",
        to_status=Booking.Status.ACCEPTED,
        actor=actor,
    )
    _notify(
        service_request.customer,
        Notification.Kind.BOOKING_UPDATE,
        "A provider accepted your service request.",
        booking,
    )
    _audit(actor, "booking.accepted", booking)
    return booking


@transaction.atomic
def create_service_offer(request_id, actor, amount, message):
    service_request = (
        ServiceRequest.objects.select_for_update()
        .select_related("category")
        .filter(pk=request_id)
        .first()
    )
    if service_request is None:
        raise ServiceRequest.DoesNotExist
    if service_request.status != ServiceRequest.Status.OPEN:
        raise Conflict("This request is no longer accepting offers.")
    if service_request.pricing_model != ServiceRequest.PricingModel.QUOTE:
        raise ValidationError(
            {"pricing_model": "This request does not accept provider quotes."}
        )
    profile = _provider_profile(actor)
    _ensure_provider_eligible(profile, service_request)
    offer = ServiceOffer.objects.create(
        service_request=service_request,
        provider=profile,
        amount=amount,
        message=message,
    )
    _notify(
        service_request.customer,
        Notification.Kind.SERVICE_OFFER,
        "A provider sent a quote for your service request.",
        service_request=service_request,
    )
    _audit(actor, "service_offer.created", offer)
    return offer


@transaction.atomic
def decide_service_offer(offer_id, actor, accept):
    offer = (
        ServiceOffer.objects.select_for_update()
        .select_related("service_request", "provider", "provider__user")
        .filter(pk=offer_id)
        .first()
    )
    if offer is None:
        raise ServiceOffer.DoesNotExist
    service_request = (
        ServiceRequest.objects.select_for_update()
        .select_related("customer", "category")
        .get(pk=offer.service_request_id)
    )
    if service_request.customer_id != actor.id:
        raise PermissionDenied("This offer is not available.")
    if offer.status != ServiceOffer.Status.PENDING:
        raise Conflict("This offer has already been decided.")
    if not accept:
        offer.status = ServiceOffer.Status.DECLINED
        offer.save(update_fields=["status", "updated_at"])
        _audit(actor, "service_offer.declined", offer)
        return None
    if service_request.status != ServiceRequest.Status.OPEN:
        raise Conflict("This request has already been accepted or cancelled.")

    profile = ProviderProfile.objects.select_for_update().get(pk=offer.provider_id)
    if (
        profile.approval_status != ProviderProfile.ApprovalStatus.APPROVED
        or not profile.is_available
        or not profile.user.is_active
        or not profile.user.is_phone_verified
    ):
        raise Conflict("The provider is no longer eligible for this request.")
    _ensure_provider_eligible(profile, service_request)
    fee_rule, customer_fee, provider_fee = _fee_values(_current_fee_rule())
    booking = Booking.objects.create(
        service_request=service_request,
        service_offer=offer,
        provider=profile,
        agreed_amount=offer.amount,
        fee_rule=fee_rule,
        customer_fee=customer_fee,
        provider_fee=provider_fee,
    )
    service_request.status = ServiceRequest.Status.ACCEPTED
    service_request.save(update_fields=["status", "updated_at"])
    offer.status = ServiceOffer.Status.ACCEPTED
    offer.save(update_fields=["status", "updated_at"])
    ServiceOffer.objects.filter(
        service_request=service_request,
        status=ServiceOffer.Status.PENDING,
    ).exclude(pk=offer.pk).update(status=ServiceOffer.Status.REVOKED)
    BookingStatusHistory.objects.create(
        booking=booking,
        from_status="",
        to_status=Booking.Status.ACCEPTED,
        actor=actor,
    )
    _notify(
        profile.user,
        Notification.Kind.BOOKING_UPDATE,
        "The customer accepted your service quote.",
        booking,
    )
    _audit(actor, "service_offer.accepted", offer)
    _audit(actor, "booking.accepted", booking)
    return booking


@transaction.atomic
def cancel_service_request(request_id, actor):
    service_request = (
        ServiceRequest.objects.select_for_update()
        .filter(pk=request_id)
        .first()
    )
    if service_request is None:
        raise ServiceRequest.DoesNotExist
    if service_request.customer_id != actor.id:
        raise PermissionDenied("This request is not available.")
    if service_request.status != ServiceRequest.Status.OPEN:
        raise Conflict("Only open service requests can be cancelled.")
    service_request.status = ServiceRequest.Status.CANCELLED
    service_request.save(update_fields=["status", "updated_at"])
    ServiceOffer.objects.filter(
        service_request=service_request,
        status=ServiceOffer.Status.PENDING,
    ).update(status=ServiceOffer.Status.REVOKED)
    _audit(actor, "service_request.cancelled", service_request)


BOOKING_TRANSITIONS = {
    Booking.Status.ACCEPTED: {
        Booking.Status.ARRIVING,
        Booking.Status.CANCELLED,
    },
    Booking.Status.ARRIVING: {
        Booking.Status.IN_PROGRESS,
        Booking.Status.CANCELLED,
        Booking.Status.DISPUTED,
    },
    Booking.Status.IN_PROGRESS: {
        Booking.Status.COMPLETION_PENDING,
        Booking.Status.DISPUTED,
    },
    Booking.Status.COMPLETION_PENDING: {
        Booking.Status.COMPLETED,
        Booking.Status.DISPUTED,
    },
}


@transaction.atomic
def transition_booking(booking_id, actor, next_status):
    booking = (
        Booking.objects.select_for_update()
        .select_related("service_request", "service_request__customer", "provider")
        .filter(pk=booking_id)
        .first()
    )
    if booking is None:
        raise Booking.DoesNotExist
    is_customer = booking.service_request.customer_id == actor.id
    is_provider = booking.provider.user_id == actor.id
    if not is_customer and not is_provider:
        raise PermissionDenied("This booking is not available.")
    if next_status not in BOOKING_TRANSITIONS.get(booking.status, set()):
        raise Conflict("This booking status transition is not allowed.")

    provider_actions = {
        Booking.Status.ARRIVING,
        Booking.Status.IN_PROGRESS,
        Booking.Status.COMPLETION_PENDING,
    }
    if next_status in provider_actions and not is_provider:
        raise PermissionDenied("Only the assigned provider can update this status.")
    if next_status == Booking.Status.COMPLETED and not is_customer:
        raise PermissionDenied("Only the customer can confirm completion.")
    if next_status == Booking.Status.CANCELLED and booking.status not in {
        Booking.Status.ACCEPTED,
        Booking.Status.ARRIVING,
    }:
        raise Conflict("This booking can no longer be cancelled.")

    previous_status = booking.status
    booking.status = next_status
    if next_status == Booking.Status.COMPLETED:
        booking.completed_at = timezone.now()
        booking.save(update_fields=["status", "completed_at", "updated_at"])
        _create_fee_entries(booking)
    else:
        booking.save(update_fields=["status", "updated_at"])
    BookingStatusHistory.objects.create(
        booking=booking,
        from_status=previous_status,
        to_status=next_status,
        actor=actor,
    )
    _notify(
        booking.service_request.customer,
        Notification.Kind.BOOKING_UPDATE,
        f"Your service booking is now {booking.get_status_display().lower()}.",
        booking,
    )
    if booking.provider.user_id != actor.id:
        _notify(
            booking.provider.user,
            Notification.Kind.BOOKING_UPDATE,
            f"A service booking is now {booking.get_status_display().lower()}.",
            booking,
        )
    _audit(actor, f"booking.{next_status.lower()}", booking)
    return booking


def _create_fee_entries(booking):
    fee_by_party = {
        FeeLedgerEntry.Party.CUSTOMER: booking.customer_fee,
        FeeLedgerEntry.Party.PROVIDER: booking.provider_fee,
    }
    for party, amount in fee_by_party.items():
        if amount > 0:
            FeeLedgerEntry.objects.get_or_create(
                booking=booking,
                party=party,
                defaults={"amount": amount, "currency": booking.currency},
            )


@transaction.atomic
def record_cash_payment(booking_id, actor):
    booking = (
        Booking.objects.select_for_update()
        .select_related("provider", "service_request")
        .filter(pk=booking_id)
        .first()
    )
    if booking is None:
        raise Booking.DoesNotExist
    if booking.provider.user_id != actor.id:
        raise PermissionDenied("Only the assigned provider can record cash received.")
    if booking.status != Booking.Status.COMPLETED:
        raise Conflict("Cash can only be recorded after service completion.")
    payment, created = CashPayment.objects.get_or_create(
        booking=booking,
        defaults={
            "recorded_by": actor,
            "amount": booking.agreed_amount,
            "currency": booking.currency,
        },
    )
    if created:
        _audit(actor, "cash_payment.recorded", payment)
    return payment, created


@transaction.atomic
def create_review(booking_id, actor, rating, comment):
    booking = (
        Booking.objects.select_for_update()
        .select_related("service_request", "provider")
        .filter(pk=booking_id)
        .first()
    )
    if booking is None:
        raise Booking.DoesNotExist
    if booking.service_request.customer_id != actor.id:
        raise PermissionDenied("Only the customer can review this booking.")
    if booking.status != Booking.Status.COMPLETED:
        raise Conflict("A review is available only after service completion.")
    review = Review.objects.create(
        booking=booking,
        customer=actor,
        provider=booking.provider,
        rating=rating,
        comment=comment,
    )
    _audit(actor, "review.created", review)
    return review
