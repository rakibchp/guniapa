from django.contrib.auth import authenticate
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.models import ProviderProfile, User
from apps.accounts.otp_service import (
    OTPRequestLimitError,
    create_phone_otp,
    invalidate_active_phone_otps,
    verify_phone_otp,
)
from apps.accounts.permissions import IsVerifiedProvider
from apps.accounts.provider_serializers import (
    ProviderProfileSerializer,
    PublicProviderSerializer,
)
from apps.accounts.serializers import (
    LogoutSerializer,
    SendOTPSerializer,
    UserLoginSerializer,
    UserRegistrationSerializer,
    VerifyOTPSerializer,
)
from apps.accounts.sms import SMSDeliveryError, deliver_phone_otp

class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            return Response(
                {
                    "message": "Account created successfully.",
                    "user": {
                        "id": str(user.id),
                        "full_name": user.full_name,
                        "email": user.email,
                        "phone_number": user.phone_number,
                        "role": user.role,
                        "is_phone_verified": user.is_phone_verified,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": "Registration failed.",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserLoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        identifier = serializer.validated_data["identifier"].strip()
        password = serializer.validated_data["password"]

        user = authenticate(
            request=request,
            username=identifier,
            password=password,
        )

        if user is not None and not user.is_phone_verified:
            return Response(
        {
            "message": "Please verify your phone number before logging in."
        },
             status=status.HTTP_403_FORBIDDEN
        )

        if user is None:
            return Response(
                {"message": "Invalid login credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Login successful.",
                "user": {
                    "id": str(user.id),
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                    "role": user.role,
                    "is_phone_verified": user.is_phone_verified,
                },
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_200_OK,
        )


class SendPhoneOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_otp"

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        phone_number = serializer.validated_data["phone_number"]

        User = get_user_model()

        user = User.objects.filter(
            phone_number=phone_number
        ).first()

        if user is None or user.is_phone_verified:
            return Response(
                {"message": "If this number can be verified, a code will be sent."},
                status=status.HTTP_200_OK,
            )

        try:
            otp = create_phone_otp(user)
        except OTPRequestLimitError as error:
            return Response(
                {"message": str(error)},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            deliver_phone_otp(phone_number, otp)
        except (ImproperlyConfigured, SMSDeliveryError):
            invalidate_active_phone_otps(user)
            return Response(
                {"message": "Phone verification is temporarily unavailable."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        response_data = {
            "message": "If this number can be verified, a code will be sent."
        }

        # Development testing only.
        if settings.DEBUG:
            response_data["development_otp"] = otp

        return Response(
            response_data,
            status=status.HTTP_200_OK
        )


class VerifyPhoneOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_otp"

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        phone_number = serializer.validated_data["phone_number"]
        submitted_otp = serializer.validated_data["otp"]

        User = get_user_model()

        user = User.objects.filter(
            phone_number=phone_number
        ).first()

        if user is None:
            return Response(
                {"message": "Unable to verify this request."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_phone_verified:
            return Response(
                {"message": "Phone number is already verified."},
                status=status.HTTP_400_BAD_REQUEST
            )

        success, message = verify_phone_otp(
            user,
            submitted_otp
        )

        if not success:
            return Response(
                {"message": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_phone_verified = True
        user.save(update_fields=["is_phone_verified"])

        return Response(
            {
                "message": "Phone number verified successfully.",
                "is_phone_verified": True
            },
            status=status.HTTP_200_OK
        )

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            refresh_token = RefreshToken(
                serializer.validated_data["refresh"]
            )

            if str(refresh_token["user_id"]) != str(request.user.id):
                return Response(
                    {"message": "Invalid refresh token."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            refresh_token.blacklist()

            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK
            )

        except TokenError:
            return Response(
                {"message": "Invalid or expired refresh token."},
                status=status.HTTP_400_BAD_REQUEST
            )



class ProviderProfileView(APIView):

    permission_classes = [IsVerifiedProvider]

    def get(self, request):
        try:
            profile = ProviderProfile.objects.get(
                user=request.user
            )

            serializer = ProviderProfileSerializer(profile)

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        except ProviderProfile.DoesNotExist:
            return Response(
                {"message": "Provider profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        if ProviderProfile.objects.filter(
            user=request.user
        ).exists():
            return Response(
                {"message": "Provider profile already exists."},
                status=status.HTTP_409_CONFLICT
            )

        serializer = ProviderProfileSerializer(
            data=request.data
        )

        if serializer.is_valid():
            profile = serializer.save(user=request.user)

            return Response(
                {
                    "message": "Provider profile created successfully.",
                    "data": ProviderProfileSerializer(profile).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "message": "Provider profile validation failed.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    def patch(self, request):
        try:
            profile = ProviderProfile.objects.get(
                user=request.user
            )

        except ProviderProfile.DoesNotExist:
            return Response(
                {"message": "Provider profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProviderProfileSerializer(
            profile,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            profile = serializer.save()

            return Response(
                {
                    "message": "Provider profile updated successfully.",
                    "data": ProviderProfileSerializer(profile).data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "message": "Provider profile validation failed.",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class PublicProviderListView(ListAPIView):

    serializer_class = PublicProviderSerializer
    permission_classes = [AllowAny]

    queryset = ProviderProfile.objects.filter(
        approval_status=ProviderProfile.ApprovalStatus.APPROVED,
        is_available=True,
        user__role=User.Role.PROVIDER,
        user__is_active=True,
        user__is_phone_verified=True,
    ).select_related("user").order_by("-created_at")


class PublicProviderDetailView(RetrieveAPIView):

    serializer_class = PublicProviderSerializer
    permission_classes = [AllowAny]

    lookup_field = "id"
    lookup_url_kwarg = "provider_id"

    queryset = ProviderProfile.objects.filter(
        approval_status=ProviderProfile.ApprovalStatus.APPROVED,
        is_available=True,
        user__role=User.Role.PROVIDER,
        user__is_active=True,
        user__is_phone_verified=True,
    ).select_related("user")


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "is_phone_verified": user.is_phone_verified,
                "is_email_verified": user.is_email_verified,
            },
            status=status.HTTP_200_OK,
        )


class ThrottledTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"
