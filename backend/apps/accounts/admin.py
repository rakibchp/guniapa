from django.contrib import admin

from apps.accounts.models import ProviderProfile


@admin.register(ProviderProfile)
class ProviderProfileAdmin(admin.ModelAdmin):
    list_display = (
        "professional_title",
        "user",
        "city",
        "approval_status",
        "is_available",
        "created_at",
    )
    list_filter = ("approval_status", "is_available", "city")
    search_fields = ("user__full_name", "user__email", "professional_title", "city")
    readonly_fields = ("id", "created_at", "updated_at")
