from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import ProviderProfile, User
from apps.marketplace.models import (
    Booking,
    CashPayment,
    FeeLedgerEntry,
    FeeRule,
    Notification,
    ProviderSkill,
    Review,
    ServiceCategory,
    ServiceOffer,
    ServiceRequest,
)


PASSWORD = "High-strength-Guniapa-123!"


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "PAGE_SIZE": 20,
    }
)
class MarketplaceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = self.create_user(
            "customer@example.com",
            "+8801712345601",
            User.Role.CUSTOMER,
        )
        self.provider = self.create_user(
            "provider@example.com",
            "+8801712345602",
            User.Role.PROVIDER,
        )
        self.profile = ProviderProfile.objects.create(
            user=self.provider,
            professional_title="Home services provider",
            approval_status=ProviderProfile.ApprovalStatus.APPROVED,
            is_available=True,
        )
        self.category = ServiceCategory.objects.create(
            name="Home services",
            slug="home-services",
            region_code="BD",
            is_active=True,
        )
        self.skill = ProviderSkill.objects.create(
            provider=self.profile,
            category=self.category,
            approval_status=ProviderSkill.ApprovalStatus.APPROVED,
        )
        self.service_request = self.create_request()

    def create_user(self, email, phone_number, role):
        return User.objects.create_user(
            email=email,
            phone_number=phone_number,
            full_name=email.split("@")[0].title(),
            password=PASSWORD,
            role=role,
            is_phone_verified=True,
        )

    def create_request(self, pricing_model=ServiceRequest.PricingModel.FIXED):
        return ServiceRequest.objects.create(
            customer=self.customer,
            category=self.category,
            details="Please help clean the kitchen and living room.",
            service_city="Dhaka",
            service_address="Private address, Dhaka",
            requested_for=timezone.now() + timedelta(days=1),
            pricing_model=pricing_model,
            proposed_amount=Decimal("1200.00")
            if pricing_model != ServiceRequest.PricingModel.QUOTE
            else None,
            duration_hours=Decimal("2.00")
            if pricing_model == ServiceRequest.PricingModel.HOURLY
            else None,
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_customer_can_create_request_and_provider_feed_hides_address(self):
        self.authenticate(self.customer)
        response = self.client.post(
            "/api/v1/requests/",
            {
                "category": str(self.category.id),
                "details": "Help with weekly cleaning.",
                "service_city": "Dhaka",
                "service_address": "Private address, Dhaka",
                "requested_for": (timezone.now() + timedelta(days=2)).isoformat(),
                "pricing_model": "FIXED",
                "proposed_amount": "1500.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], ServiceRequest.Status.OPEN)

        self.authenticate(self.provider)
        available = self.client.get("/api/v1/requests/available/")
        self.assertEqual(available.status_code, 200)
        self.assertEqual(available.data["count"], 2)
        item = available.data["results"][0]
        self.assertEqual(item["service_city"], "Dhaka")
        self.assertNotIn("service_address", item)
        self.assertNotIn("customer", item)

    def test_only_eligible_verified_skill_can_accept_and_booking_is_scoped(self):
        self.authenticate(self.provider)
        accepted = self.client.post(
            f"/api/v1/requests/{self.service_request.id}/accept/",
            {},
            format="json",
        )
        self.assertEqual(accepted.status_code, 201)
        booking_id = accepted.data["id"]
        self.assertEqual(accepted.data["status"], Booking.Status.ACCEPTED)
        self.assertEqual(accepted.data["service_address"], "Private address, Dhaka")

        other_provider = self.create_user(
            "other@example.com",
            "+8801712345603",
            User.Role.PROVIDER,
        )
        other_profile = ProviderProfile.objects.create(
            user=other_provider,
            approval_status=ProviderProfile.ApprovalStatus.APPROVED,
            is_available=True,
        )
        ProviderSkill.objects.create(
            provider=other_profile,
            category=self.category,
            approval_status=ProviderSkill.ApprovalStatus.APPROVED,
        )
        self.client.force_authenticate(user=other_provider)
        conflict = self.client.post(
            f"/api/v1/requests/{self.service_request.id}/accept/",
            {},
            format="json",
        )
        self.assertEqual(conflict.status_code, 409)

        other_customer = self.create_user(
            "other-customer@example.com",
            "+8801712345604",
            User.Role.CUSTOMER,
        )
        self.client.force_authenticate(user=other_customer)
        denied = self.client.get(f"/api/v1/bookings/{booking_id}/")
        self.assertEqual(denied.status_code, 404)

    def test_completion_cash_recording_and_fee_ledger(self):
        rule = FeeRule.objects.create(
            version=1,
            customer_fee=Decimal("10.00"),
            provider_fee=Decimal("15.00"),
            is_active=True,
            created_by=self.customer,
        )
        self.authenticate(self.provider)
        accepted = self.client.post(
            f"/api/v1/requests/{self.service_request.id}/accept/",
            {},
            format="json",
        )
        booking_id = accepted.data["id"]
        self.assertEqual(accepted.data["customer_fee"], "10.00")
        self.assertEqual(Booking.objects.get(pk=booking_id).fee_rule, rule)

        for next_status in [
            Booking.Status.ARRIVING,
            Booking.Status.IN_PROGRESS,
            Booking.Status.COMPLETION_PENDING,
        ]:
            response = self.client.post(
                f"/api/v1/bookings/{booking_id}/transition/",
                {"status": next_status},
                format="json",
            )
            self.assertEqual(response.status_code, 200)

        provider_cannot_confirm = self.client.post(
            f"/api/v1/bookings/{booking_id}/transition/",
            {"status": Booking.Status.COMPLETED},
            format="json",
        )
        self.assertEqual(provider_cannot_confirm.status_code, 403)

        self.authenticate(self.customer)
        complete = self.client.post(
            f"/api/v1/bookings/{booking_id}/transition/",
            {"status": Booking.Status.COMPLETED},
            format="json",
        )
        self.assertEqual(complete.status_code, 200)
        self.assertEqual(FeeLedgerEntry.objects.count(), 2)

        self.authenticate(self.provider)
        cash_first = self.client.post(
            f"/api/v1/bookings/{booking_id}/cash-payment/",
            {},
            format="json",
        )
        cash_again = self.client.post(
            f"/api/v1/bookings/{booking_id}/cash-payment/",
            {},
            format="json",
        )
        self.assertEqual(cash_first.status_code, 201)
        self.assertEqual(cash_again.status_code, 200)
        self.assertEqual(CashPayment.objects.count(), 1)
        self.assertEqual(cash_first.data["amount"], "1200.00")

    def test_quote_offer_requires_customer_acceptance(self):
        quote_request = self.create_request(ServiceRequest.PricingModel.QUOTE)
        self.authenticate(self.provider)
        offer_response = self.client.post(
            f"/api/v1/requests/{quote_request.id}/offers/",
            {"amount": "950.00", "message": "Includes the requested work."},
            format="json",
        )
        self.assertEqual(offer_response.status_code, 201)
        offer_id = offer_response.data["id"]
        self.assertFalse(Booking.objects.filter(service_request=quote_request).exists())

        self.authenticate(self.customer)
        accepted = self.client.post(
            f"/api/v1/offers/{offer_id}/accept/",
            {},
            format="json",
        )
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(accepted.data["agreed_amount"], "950.00")
        self.assertEqual(
            ServiceRequest.objects.get(pk=quote_request.pk).status,
            ServiceRequest.Status.ACCEPTED,
        )
        self.assertEqual(
            ServiceOffer.objects.get(pk=offer_id).status,
            ServiceOffer.Status.ACCEPTED,
        )

    def test_credential_required_category_excludes_unverified_skill(self):
        self.category.requires_credential = True
        self.category.save(update_fields=["requires_credential"])
        self.authenticate(self.provider)

        available = self.client.get("/api/v1/requests/available/")
        self.assertEqual(available.data["count"], 0)
        accepted = self.client.post(
            f"/api/v1/requests/{self.service_request.id}/accept/",
            {},
            format="json",
        )
        self.assertEqual(accepted.status_code, 403)

    def test_review_only_after_completion_and_review_is_unique(self):
        self.authenticate(self.provider)
        booking_response = self.client.post(
            f"/api/v1/requests/{self.service_request.id}/accept/",
            {},
            format="json",
        )
        booking_id = booking_response.data["id"]
        self.authenticate(self.customer)
        early = self.client.post(
            f"/api/v1/bookings/{booking_id}/reviews/",
            {"rating": 5, "comment": "Great."},
            format="json",
        )
        self.assertEqual(early.status_code, 409)

        self.authenticate(self.provider)
        for next_status in [
            Booking.Status.ARRIVING,
            Booking.Status.IN_PROGRESS,
            Booking.Status.COMPLETION_PENDING,
        ]:
            self.client.post(
                f"/api/v1/bookings/{booking_id}/transition/",
                {"status": next_status},
                format="json",
            )
        self.authenticate(self.customer)
        self.client.post(
            f"/api/v1/bookings/{booking_id}/transition/",
            {"status": Booking.Status.COMPLETED},
            format="json",
        )
        first = self.client.post(
            f"/api/v1/bookings/{booking_id}/reviews/",
            {"rating": 5, "comment": "Great."},
            format="json",
        )
        duplicate = self.client.post(
            f"/api/v1/bookings/{booking_id}/reviews/",
            {"rating": 4, "comment": "Duplicate."},
            format="json",
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(Review.objects.count(), 1)

    def test_customer_cancellation_revokes_pending_provider_quotes(self):
        quote_request = self.create_request(ServiceRequest.PricingModel.QUOTE)
        self.authenticate(self.provider)
        offer = self.client.post(
            f"/api/v1/requests/{quote_request.id}/offers/",
            {"amount": "900.00", "message": "Available this week."},
            format="json",
        )
        self.assertEqual(offer.status_code, 201)

        self.authenticate(self.customer)
        cancelled = self.client.delete(
            f"/api/v1/requests/{quote_request.id}/",
        )
        self.assertEqual(cancelled.status_code, 204)
        quote_request.refresh_from_db()
        offer_record = ServiceOffer.objects.get(pk=offer.data["id"])
        self.assertEqual(quote_request.status, ServiceRequest.Status.CANCELLED)
        self.assertEqual(offer_record.status, ServiceOffer.Status.REVOKED)

    def test_quotes_support_tickets_and_notifications_are_user_scoped(self):
        quote_request = self.create_request(ServiceRequest.PricingModel.QUOTE)
        self.authenticate(self.provider)
        offer = self.client.post(
            f"/api/v1/requests/{quote_request.id}/offers/",
            {"amount": "900.00", "message": "Quote."},
            format="json",
        )
        self.assertEqual(offer.status_code, 201)

        other_customer = self.create_user(
            "other-customer@example.com",
            "+8801712345604",
            User.Role.CUSTOMER,
        )
        self.authenticate(other_customer)
        self.assertEqual(
            self.client.get(
                f"/api/v1/requests/{quote_request.id}/offers/",
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                f"/api/v1/offers/{offer.data['id']}/accept/",
                {},
                format="json",
            ).status_code,
            403,
        )

        self.authenticate(self.customer)
        ticket = self.client.post(
            "/api/v1/support/tickets/",
            {"subject": "Booking question", "description": "Please contact me."},
            format="json",
        )
        self.assertEqual(ticket.status_code, 201)
        notification = Notification.objects.create(
            recipient=self.customer,
            kind=Notification.Kind.SERVICE_OFFER,
            message="A provider sent a quote.",
        )

        self.authenticate(other_customer)
        self.assertEqual(
            self.client.get("/api/v1/support/tickets/").data["count"],
            0,
        )
        self.assertEqual(
            self.client.post(
                f"/api/v1/notifications/{notification.id}/read/",
                {},
                format="json",
            ).status_code,
            404,
        )
        self.authenticate(self.customer)
        self.assertEqual(
            self.client.get("/api/v1/support/tickets/").data["count"],
            1,
        )

    def test_provider_onboarding_requires_review_before_request_feed(self):
        new_provider = self.create_user(
            "new-provider@example.com",
            "+8801712345605",
            User.Role.PROVIDER,
        )
        self.authenticate(new_provider)
        profile_response = self.client.post(
            "/api/v1/providers/profile/",
            {
                "professional_title": "Home cleaning professional",
                "bio": "Experienced in home cleaning.",
                "experience_years": 4,
                "city": "Dhaka",
                "service_area": "Central Dhaka",
                "service_radius_km": 10,
            },
            format="json",
        )
        self.assertEqual(profile_response.status_code, 201)
        self.assertEqual(
            profile_response.data["data"]["approval_status"],
            ProviderProfile.ApprovalStatus.PENDING,
        )

        skill_response = self.client.post(
            "/api/v1/providers/skills/",
            {"category": str(self.category.id), "experience_years": 4},
            format="json",
        )
        self.assertEqual(skill_response.status_code, 201)
        self.assertEqual(
            skill_response.data["approval_status"],
            ProviderSkill.ApprovalStatus.PENDING,
        )
        self.assertEqual(
            self.client.get("/api/v1/requests/available/").status_code,
            403,
        )
