
from rest_framework.permissions import BasePermission


class IsVerifiedProvider(BasePermission):
    message = "Only verified service providers can access this resource."

    def has_permission(self, request, view):
        user = request.user

        return (
            user
            and user.is_authenticated
            and user.role == "PROVIDER"
            and user.is_active
            and user.is_phone_verified
        )
