from django.db import IntegrityError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ProviderProfile, User
from apps.accounts.permissions import IsVerifiedProvider
from apps.marketplace.models import (
    Booking,
    CashPayment,
    Notification,
    ProviderSkill,
    Review,
    ServiceCategory,
    ServiceOffer,
    ServiceRequest,
    SupportTicket,
)
from apps.marketplace.serializers import (
    AvailableServiceRequestSerializer,
    BookingSerializer,
    BookingTransitionSerializer,
    CashPaymentSerializer,
    NotificationSerializer,
    ProviderSkillSerializer,
    PublicReviewSerializer,
    ReviewCreateSerializer,
    ServiceCategorySerializer,
    ServiceOfferCreateSerializer,
    ServiceOfferSerializer,
    ServiceRequestCreateSerializer,
    SupportTicketCreateSerializer,
    SupportTicketSerializer,
)
from apps.marketplace.services import (
    Conflict,
    accept_fixed_price_request,
    cancel_service_request,
    create_review,
    create_service_offer,
    decide_service_offer,
    record_cash_payment,
    transition_booking,
)


class ServiceCategoryListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ServiceCategorySerializer
    queryset = ServiceCategory.objects.filter(is_active=True)


class ProviderSkillListCreateView(ListAPIView):
    permission_classes = [IsVerifiedProvider]
    serializer_class = ProviderSkillSerializer

    def get_queryset(self):
        profile = get_object_or_404(ProviderProfile, user=self.request.user)
        return ProviderSkill.objects.filter(provider=profile).select_related("category")

    def post(self, request, *args, **kwargs):
        if not request.user.is_phone_verified:
            raise PermissionDenied("Verify your phone number before adding skills.")
        profile = get_object_or_404(ProviderProfile, user=request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            skill = serializer.save(provider=profile)
        except IntegrityError:
            raise Conflict("You have already submitted this service skill.")
        return Response(
            self.get_serializer(skill).data,
            status=status.HTTP_201_CREATED,
        )


class ServiceRequestListCreateView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceRequestCreateSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.CUSTOMER:
            return (
                ServiceRequest.objects.filter(customer=user)
                .select_related("category")
                .prefetch_related("offers", "booking")
            )
        if user.role == User.Role.PROVIDER:
            return (
                ServiceRequest.objects.filter(booking__provider__user=user)
                .select_related("category")
            )
        if user.is_staff:
            return ServiceRequest.objects.all().select_related("category")
        raise PermissionDenied("This account cannot view service requests.")

    def post(self, request, *args, **kwargs):
        if request.user.role != User.Role.CUSTOMER or not request.user.is_phone_verified:
            raise PermissionDenied(
                "A phone-verified customer account is required to request a service."
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service_request = serializer.save(customer=request.user)
        return Response(
            self.get_serializer(service_request).data,
            status=status.HTTP_201_CREATED,
        )


class AvailableServiceRequestListView(ListAPIView):
    permission_classes = [IsVerifiedProvider]
    serializer_class = AvailableServiceRequestSerializer

    def get_queryset(self):
        profile = get_object_or_404(ProviderProfile, user=self.request.user)
        if (
            profile.approval_status != ProviderProfile.ApprovalStatus.APPROVED
            or not profile.is_available
        ):
            raise PermissionDenied("Your provider profile is not approved and available.")
        skills = ProviderSkill.objects.filter(
            provider=profile,
            approval_status=ProviderSkill.ApprovalStatus.APPROVED,
            category__is_active=True,
        ).filter(
            Q(category__requires_credential=False)
            | Q(credential_verified=True)
        )
        queryset = ServiceRequest.objects.filter(
            status=ServiceRequest.Status.OPEN,
            requested_for__gt=timezone.now(),
            category_id__in=skills.values("category_id"),
        ).select_related("category")
        city = self.request.query_params.get("city")
        if city:
            queryset = queryset.filter(service_city__iexact=city.strip())
        return queryset


class ServiceRequestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, request_id):
        user = request.user
        queryset = ServiceRequest.objects.select_related(
            "category",
            "customer",
            "booking",
            "booking__provider",
        )
        if user.role == User.Role.CUSTOMER:
            queryset = queryset.filter(customer=user)
        elif user.role == User.Role.PROVIDER:
            queryset = queryset.filter(booking__provider__user=user)
        elif user.is_staff:
            pass
        else:
            raise PermissionDenied("This account cannot view service requests.")
        return get_object_or_404(queryset, pk=request_id)

    def get(self, request, request_id):
        service_request = self.get_object(request, request_id)
        return Response(ServiceRequestCreateSerializer(service_request).data)

    def delete(self, request, request_id):
        service_request = self.get_object(request, request_id)
        cancel_service_request(service_request.id, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvailableServiceRequestAcceptView(APIView):
    permission_classes = [IsVerifiedProvider]

    def post(self, request, request_id):
        try:
            booking = accept_fixed_price_request(request_id, request.user)
        except ServiceRequest.DoesNotExist as error:
            raise NotFound("Service request not found.") from error
        except IntegrityError as error:
            raise Conflict("Another provider already accepted this request.") from error
        return Response(
            BookingSerializer(booking, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ServiceRequestOfferListCreateView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ServiceOfferSerializer

    def get_queryset(self):
        service_request = get_object_or_404(
            ServiceRequest,
            pk=self.kwargs["request_id"],
            customer=self.request.user,
        )
        return ServiceOffer.objects.filter(
            service_request=service_request,
        ).select_related("provider", "provider__user")

    def post(self, request, request_id):
        if request.user.role != User.Role.PROVIDER:
            raise PermissionDenied("Only providers can submit service quotes.")
        if not request.user.is_phone_verified:
            raise PermissionDenied("Verify your phone number before sending a quote.")
        service_request = get_object_or_404(
            ServiceRequest,
            pk=request_id,
            status=ServiceRequest.Status.OPEN,
            pricing_model=ServiceRequest.PricingModel.QUOTE,
        )
        serializer = ServiceOfferCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            offer = create_service_offer(
                service_request.id,
                request.user,
                serializer.validated_data["amount"],
                serializer.validated_data["message"],
            )
        except ServiceRequest.DoesNotExist as error:
            raise NotFound("Service request not found.") from error
        except IntegrityError as error:
            raise Conflict("You have already submitted a quote for this request.") from error
        return Response(
            ServiceOfferSerializer(offer).data,
            status=status.HTTP_201_CREATED,
        )


class ServiceOfferDecisionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, offer_id, decision):
        if request.user.role != User.Role.CUSTOMER:
            raise PermissionDenied("Only the customer can decide on a quote.")
        if decision not in {"accept", "decline"}:
            raise NotFound("Offer decision not found.")
        try:
            booking = decide_service_offer(
                offer_id,
                request.user,
                accept=decision == "accept",
            )
        except ServiceOffer.DoesNotExist as error:
            raise NotFound("Offer not found.") from error
        except IntegrityError as error:
            raise Conflict("The request was accepted by another action.") from error
        if booking is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            BookingSerializer(booking, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class BookingListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BookingSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Booking.objects.select_related(
            "service_request",
            "service_request__category",
            "service_request__customer",
            "provider",
            "provider__user",
        ).prefetch_related("status_history", "status_history__actor")
        if user.role == User.Role.CUSTOMER:
            return queryset.filter(service_request__customer=user)
        if user.role == User.Role.PROVIDER:
            return queryset.filter(provider__user=user)
        if user.is_staff:
            return queryset
        raise PermissionDenied("This account cannot view bookings.")


class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, user):
        queryset = Booking.objects.select_related(
            "service_request",
            "service_request__category",
            "service_request__customer",
            "provider",
            "provider__user",
        ).prefetch_related("status_history", "status_history__actor")
        if user.role == User.Role.CUSTOMER:
            return queryset.filter(service_request__customer=user)
        if user.role == User.Role.PROVIDER:
            return queryset.filter(provider__user=user)
        if user.is_staff:
            return queryset
        raise PermissionDenied("This account cannot view bookings.")

    def get(self, request, booking_id):
        booking = get_object_or_404(self.get_queryset(request.user), pk=booking_id)
        payment = getattr(booking, "cash_payment", None)
        data = BookingSerializer(booking, context={"request": request}).data
        data["cash_payment"] = (
            CashPaymentSerializer(payment).data if payment is not None else None
        )
        return Response(data)


class BookingTransitionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        serializer = BookingTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = transition_booking(
                booking_id,
                request.user,
                serializer.validated_data["status"],
            )
        except Booking.DoesNotExist as error:
            raise NotFound("Booking not found.") from error
        data = BookingSerializer(booking, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)


class CashPaymentRecordView(APIView):
    permission_classes = [IsVerifiedProvider]

    def post(self, request, booking_id):
        try:
            payment, created = record_cash_payment(booking_id, request.user)
        except Booking.DoesNotExist as error:
            raise NotFound("Booking not found.") from error
        return Response(
            CashPaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        if request.user.role != User.Role.CUSTOMER:
            raise PermissionDenied("Only customers can review completed services.")
        serializer = ReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            review = create_review(
                booking_id,
                request.user,
                serializer.validated_data["rating"],
                serializer.validated_data["comment"],
            )
        except Booking.DoesNotExist as error:
            raise NotFound("Booking not found.") from error
        except IntegrityError as error:
            raise Conflict("This booking already has a review.") from error
        return Response(
            PublicReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class ProviderReviewListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicReviewSerializer

    def get_queryset(self):
        profile = get_object_or_404(
            ProviderProfile.objects.filter(
                approval_status=ProviderProfile.ApprovalStatus.APPROVED,
                is_available=True,
                user__role=User.Role.PROVIDER,
                user__is_active=True,
                user__is_phone_verified=True,
            ),
            pk=self.kwargs["provider_id"],
        )
        return Review.objects.filter(
            provider=profile,
            moderation_status=Review.ModerationStatus.PUBLISHED,
        ).select_related("customer")


class SupportTicketListCreateView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SupportTicketSerializer

    def get_queryset(self):
        queryset = SupportTicket.objects.select_related("booking")
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(opened_by=self.request.user)

    def post(self, request, *args, **kwargs):
        serializer = SupportTicketCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save(opened_by=request.user)
        return Response(
            SupportTicketSerializer(ticket).data,
            status=status.HTTP_201_CREATED,
        )


class NotificationListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(
            Notification,
            pk=notification_id,
            recipient=request.user,
        )
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)
