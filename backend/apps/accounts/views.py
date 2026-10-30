from django.shortcuts import render

# Create your views here.

from django.contrib.auth import authenticate

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.accounts.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
)


from django.conf import settings
from django.contrib.auth import get_user_model

from apps.accounts.otp_service import (
    create_phone_otp,
    verify_phone_otp
)
from apps.accounts.serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer
)



class UserRegistrationView(APIView):

    permission_classes = [AllowAny]

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

        if user is None:
            return Response(
                {"message": "Unable to process this request."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_phone_verified:
            return Response(
                {"message": "Phone number is already verified."},
                status=status.HTTP_400_BAD_REQUEST
            )

        otp = create_phone_otp(user)

        response_data = {
            "message": "OTP request processed."
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
