from django.test import TestCase, override_settings
from django.core.cache import cache
from unittest.mock import patch
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import ProviderProfile, User


PASSWORD = "High-strength-Guniapa-123!"


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ],
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
        "PAGE_SIZE": 20,
        "DEFAULT_THROTTLE_CLASSES": [],
    }
)
class AccountApiTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def register(self, **overrides):
        payload = {
            "full_name": "Ayesha Rahman",
            "email": "ayesha@example.com",
            "phone_number": "+8801712345678",
            "password": PASSWORD,
            "role": User.Role.CUSTOMER,
        }
        payload.update(overrides)
        return self.client.post("/api/v1/auth/register/", payload, format="json")

    def create_user(self, **overrides):
        values = {
            "full_name": "Ayesha Rahman",
            "email": "ayesha@example.com",
            "phone_number": "+8801712345678",
            "role": User.Role.CUSTOMER,
            "is_phone_verified": True,
        }
        values.update(overrides)
        user = User.objects.create_user(password=PASSWORD, **values)
        return user

    def test_registration_hashes_password_and_does_not_verify_phone(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="ayesha@example.com")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotEqual(user.password, PASSWORD)
        self.assertFalse(user.is_phone_verified)
        self.assertNotIn("password", response.data["user"])

    def test_public_registration_cannot_assign_admin_role(self):
        response = self.register(role=User.Role.ADMIN)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())

    def test_login_requires_phone_verification(self):
        self.create_user(is_phone_verified=False)

        response = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": "ayesha@example.com", "password": PASSWORD},
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertNotIn("tokens", response.data)

    def test_login_current_user_refresh_and_logout(self):
        user = self.create_user()
        login = self.client.post(
            "/api/v1/auth/login/",
            {"identifier": user.email, "password": PASSWORD},
            format="json",
        )
        self.assertEqual(login.status_code, 200)

        access = login.data["tokens"]["access"]
        refresh = login.data["tokens"]["refresh"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        current_user = self.client.get("/api/v1/auth/me/")
        self.assertEqual(current_user.status_code, 200)
        self.assertEqual(current_user.data["id"], str(user.id))
        self.assertEqual(current_user.data["role"], User.Role.CUSTOMER)

        self.client.credentials()
        refreshed = self.client.post(
            "/api/v1/auth/refresh/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn("access", refreshed.data)
        self.assertIn("refresh", refreshed.data)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {refreshed.data['access']}"
        )
        logout = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": refreshed.data["refresh"]},
            format="json",
        )
        self.assertEqual(logout.status_code, 200)

        refresh_reuse = self.client.post(
            "/api/v1/auth/refresh/",
            {"refresh": refreshed.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_reuse.status_code, 401)

    @override_settings(DEBUG=True)
    def test_phone_otp_can_be_requested_and_verified(self):
        user = self.create_user(is_phone_verified=False)
        sent = self.client.post(
            "/api/v1/auth/otp/send/",
            {"phone_number": user.phone_number},
            format="json",
        )
        self.assertEqual(sent.status_code, 200)
        self.assertIn("development_otp", sent.data)

        verified = self.client.post(
            "/api/v1/auth/otp/verify/",
            {
                "phone_number": user.phone_number,
                "otp": sent.data["development_otp"],
            },
            format="json",
        )
        self.assertEqual(verified.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_phone_verified)

    def test_logout_cannot_revoke_another_users_refresh_token(self):
        user = self.create_user()
        other_user = self.create_user(
            email="other@example.com",
            phone_number="+8801712345679",
        )
        own_access = str(RefreshToken.for_user(user).access_token)
        other_refresh = str(RefreshToken.for_user(other_user))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {own_access}")

        response = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": other_refresh},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_public_provider_list_excludes_unapproved_and_private_details(self):
        provider = self.create_user(
            email="provider@example.com",
            phone_number="+8801712345679",
            role=User.Role.PROVIDER,
        )
        ProviderProfile.objects.create(
            user=provider,
            approval_status=ProviderProfile.ApprovalStatus.APPROVED,
            is_available=True,
            city="Dhaka",
            service_area="Private address detail",
        )
        unapproved = self.create_user(
            email="pending@example.com",
            phone_number="+8801712345680",
            role=User.Role.PROVIDER,
        )
        ProviderProfile.objects.create(
            user=unapproved,
            is_available=True,
        )

        response = self.client.get("/api/v1/providers/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["city"], "Dhaka")
        self.assertNotIn("service_area", response.data["results"][0])

    def test_unknown_otp_target_returns_generic_response(self):
        response = self.client.post(
            "/api/v1/auth/otp/send/",
            {"phone_number": "+8801712345688"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("development_otp", response.data)

    def test_otp_send_is_rate_limited(self):
        with patch(
            "rest_framework.throttling.ScopedRateThrottle.THROTTLE_RATES",
            {"auth_otp": "1/hour"},
        ):
            first = self.client.post(
                "/api/v1/auth/otp/send/",
                {"phone_number": "+8801712345688"},
                format="json",
            )
            second = self.client.post(
                "/api/v1/auth/otp/send/",
                {"phone_number": "+8801712345688"},
                format="json",
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)
