from django.contrib import admin

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
    ServiceCategory,
    ServiceOffer,
    ServiceRequest,
    SupportTicket,
)


class AuditedAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        AuditEvent.objects.create(
            actor=request.user,
            action=f"{obj._meta.model_name}.{'updated' if change else 'created'}",
            target_type=obj.__class__.__name__,
            target_id=str(obj.pk),
        )


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(AuditedAdmin):
    list_display = ("name", "region_code", "requires_credential", "is_active")
    list_filter = ("region_code", "requires_credential", "is_active")
    search_fields = ("name", "slug")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ProviderSkill)
class ProviderSkillAdmin(AuditedAdmin):
    list_display = (
        "provider",
        "category",
        "approval_status",
        "credential_verified",
        "created_at",
    )
    list_filter = ("approval_status", "credential_verified", "category")
    search_fields = ("provider__user__full_name", "provider__user__email", "category__name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(FeeRule)
class FeeRuleAdmin(AuditedAdmin):
    list_display = (
        "version",
        "customer_fee",
        "provider_fee",
        "currency",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "currency")
    readonly_fields = ("created_at",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "category", "service_city", "status", "created_at")
    list_filter = ("status", "category", "service_city")
    search_fields = ("id", "customer__email", "customer__full_name", "details")
    readonly_fields = tuple(field.name for field in ServiceRequest._meta.fields)
    date_hierarchy = "created_at"


@admin.register(ServiceOffer)
class ServiceOfferAdmin(admin.ModelAdmin):
    list_display = ("id", "service_request", "provider", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    readonly_fields = tuple(field.name for field in ServiceOffer._meta.fields)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "service_request", "provider", "status", "agreed_amount", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("id", "service_request__customer__email", "provider__user__email")
    readonly_fields = tuple(field.name for field in Booking._meta.fields)
    date_hierarchy = "created_at"


@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("booking", "from_status", "to_status", "actor", "created_at")
    list_filter = ("to_status", "created_at")
    readonly_fields = tuple(field.name for field in BookingStatusHistory._meta.fields)


@admin.register(FeeLedgerEntry)
class FeeLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("booking", "party", "amount", "currency", "created_at")
    list_filter = ("party", "currency")
    readonly_fields = tuple(field.name for field in FeeLedgerEntry._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CashPayment)
class CashPaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "recorded_by", "amount", "currency", "received_at")
    readonly_fields = tuple(field.name for field in CashPayment._meta.fields)


@admin.register(Review)
class ReviewAdmin(AuditedAdmin):
    list_display = ("provider", "customer", "rating", "moderation_status", "created_at")
    list_filter = ("moderation_status", "rating", "created_at")
    search_fields = ("provider__user__full_name", "customer__full_name", "comment")
    readonly_fields = ("id", "booking", "customer", "provider", "rating", "comment", "created_at")


@admin.register(SupportTicket)
class SupportTicketAdmin(AuditedAdmin):
    list_display = ("subject", "opened_by", "status", "assigned_to", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("subject", "opened_by__email", "description")
    readonly_fields = ("id", "opened_by", "booking", "subject", "description", "created_at", "updated_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "kind", "is_read", "created_at")
    list_filter = ("kind", "is_read", "created_at")
    readonly_fields = tuple(field.name for field in Notification._meta.fields)


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("actor", "action", "target_type", "target_id", "created_at")
    list_filter = ("action", "target_type", "created_at")
    readonly_fields = tuple(field.name for field in AuditEvent._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
