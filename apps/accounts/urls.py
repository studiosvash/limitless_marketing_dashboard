from django.urls import path

from .views import (
    AcceptInviteView,
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Target of the invitation email. Public by necessity: the invitee has no account yet.
    path("accept-invite/", AcceptInviteView.as_view(), name="accept-invite"),
    # Names match Django's defaults (password_reset_confirm etc.) because the built-in
    # views and PasswordResetForm reverse them by those names.
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/sent/", PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
