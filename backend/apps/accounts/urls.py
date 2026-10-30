
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
    VerifyPhoneOTPView
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view()),
    path("login/", UserLoginView.as_view()),
    path("otp/send/", SendPhoneOTPView.as_view()),
    path("otp/verify/", VerifyPhoneOTPView.as_view()),
]
