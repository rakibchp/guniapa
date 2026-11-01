
# from django.urls import path

# from apps.accounts.views import (
#     UserRegistrationView,
#     UserLoginView,
# )

# urlpatterns = [
#     path("register/", UserRegistrationView.as_view(), name="register"),
#     path("login/", UserLoginView.as_view(), name="login"),
# ]


from django.urls import path

from apps.accounts.views import (
    UserRegistrationView,
    UserLoginView,
    SendPhoneOTPView,
    VerifyPhoneOTPView,
    UserLogoutView,
    CurrentUserView,
    ThrottledTokenRefreshView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view()),
    path("login/", UserLoginView.as_view()),
    path("refresh/", ThrottledTokenRefreshView.as_view()),
    path("me/", CurrentUserView.as_view()),
    path("otp/send/", SendPhoneOTPView.as_view()),
    path("otp/verify/", VerifyPhoneOTPView.as_view()),
    path("logout/", UserLogoutView.as_view()),
]
