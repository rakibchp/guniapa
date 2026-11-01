from django.urls import path

from apps.marketplace.views import (
    AvailableServiceRequestAcceptView,
    AvailableServiceRequestListView,
    BookingDetailView,
    BookingListView,
    BookingTransitionView,
    CashPaymentRecordView,
    NotificationListView,
    NotificationReadView,
    ProviderReviewListView,
    ProviderSkillListCreateView,
    ReviewCreateView,
    ServiceCategoryListView,
    ServiceOfferDecisionView,
    ServiceRequestDetailView,
    ServiceRequestListCreateView,
    ServiceRequestOfferListCreateView,
    SupportTicketListCreateView,
)

urlpatterns = [
    path("categories/", ServiceCategoryListView.as_view(), name="service-category-list"),
    path("providers/skills/", ProviderSkillListCreateView.as_view(), name="provider-skills"),
    path(
        "providers/<uuid:provider_id>/reviews/",
        ProviderReviewListView.as_view(),
        name="provider-reviews",
    ),
    path(
        "requests/available/",
        AvailableServiceRequestListView.as_view(),
        name="available-service-requests",
    ),
    path(
        "requests/<uuid:request_id>/offers/",
        ServiceRequestOfferListCreateView.as_view(),
        name="service-request-offers",
    ),
    path(
        "requests/<uuid:request_id>/accept/",
        AvailableServiceRequestAcceptView.as_view(),
        name="accept-service-request",
    ),
    path(
        "requests/<uuid:request_id>/",
        ServiceRequestDetailView.as_view(),
        name="service-request-detail",
    ),
    path(
        "requests/",
        ServiceRequestListCreateView.as_view(),
        name="service-request-list",
    ),
    path(
        "offers/<uuid:offer_id>/accept/",
        ServiceOfferDecisionView.as_view(),
        {"decision": "accept"},
        name="accept-service-offer",
    ),
    path(
        "offers/<uuid:offer_id>/decline/",
        ServiceOfferDecisionView.as_view(),
        {"decision": "decline"},
        name="decline-service-offer",
    ),
    path("bookings/", BookingListView.as_view(), name="booking-list"),
    path(
        "bookings/<uuid:booking_id>/",
        BookingDetailView.as_view(),
        name="booking-detail",
    ),
    path(
        "bookings/<uuid:booking_id>/transition/",
        BookingTransitionView.as_view(),
        name="booking-transition",
    ),
    path(
        "bookings/<uuid:booking_id>/cash-payment/",
        CashPaymentRecordView.as_view(),
        name="cash-payment-record",
    ),
    path(
        "bookings/<uuid:booking_id>/reviews/",
        ReviewCreateView.as_view(),
        name="booking-review",
    ),
    path("support/tickets/", SupportTicketListCreateView.as_view(), name="support-tickets"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path(
        "notifications/<uuid:notification_id>/read/",
        NotificationReadView.as_view(),
        name="notification-read",
    ),
]
