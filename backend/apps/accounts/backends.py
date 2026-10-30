
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.db.models import Q


class EmailOrPhoneBackend(BaseBackend):

    def authenticate(
        self,
        request,
        username=None,
        password=None,
        **kwargs
    ):
        User = get_user_model()

        identifier = username or kwargs.get("email")

        if not identifier or not password:
            return None

        try:
            user = User.objects.get(
                Q(email__iexact=identifier) |
                Q(phone_number=identifier)
            )
        except User.DoesNotExist:
            # Perform a password hash operation to reduce timing differences.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def user_can_authenticate(self, user):
        return user.is_active
