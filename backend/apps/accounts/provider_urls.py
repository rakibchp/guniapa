
from django.urls import path

from apps.accounts.views import (
    ProviderProfileView,
    PublicProviderListView,
    PublicProviderDetailView
)

urlpatterns = [
    path(
        "profile/",
        ProviderProfileView.as_view(),
        name="provider-profile"
    ),
    path(
        "",
        PublicProviderListView.as_view(),
        name="provider-list"
    ),
    path(
        "<uuid:provider_id>/",
        PublicProviderDetailView.as_view(),
        name="provider-detail"
    ),
]
