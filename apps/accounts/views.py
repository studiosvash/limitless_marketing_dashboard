"""Authentication views. Thin wrappers over Django's built-in auth so we get a
branded login page while keeping Django's secure session handling.

Every view here is marked `login_not_required` so it stays reachable under
LoginRequiredMiddleware (which otherwise protects every view by default). That decorator is
the whole reason these exist as subclasses rather than as `auth_views.*` straight in urls.py:
without it an invitee clicking their emailed link, or anyone who forgot their password, is
302'd to the login page they cannot get past.
"""

from django.contrib.auth import login as auth_login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View

from .services import InvitationError, accept_invitation, get_valid_invitation


@method_decorator(login_not_required, name="dispatch")
class LoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


from django.contrib.auth import logout as auth_logout
from django.views.decorators.csrf import csrf_exempt


@method_decorator([login_not_required, csrf_exempt], name="dispatch")
class LogoutView(View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            auth_logout(request)
        return redirect("/login/")


@method_decorator(login_not_required, name="dispatch")
class AcceptInviteView(View):
    """`GET|POST /accept-invite/?token=...` — where the invitation email lands.

    Server-rendered rather than a route inside the SPA: the SPA is served from `/`, which is
    login-protected, so an invitee following `#/accept-invite?token=...` was bounced to the
    sign-in form and had no way past it — no account existed yet. (The URL fragment never
    reaches the server either, so the middleware could not have made an exception for it.)

    The form only asks for a password. The username is the invited email address and the
    role was fixed when the invite was sent, so there is nothing else for the invitee to
    decide. On success they are signed in and dropped straight into the dashboard.
    """

    template_name = "registration/accept_invite.html"

    def get(self, request):
        token = request.GET.get("token", "")
        try:
            invitation = get_valid_invitation(token)
        except InvitationError as exc:
            return render(request, self.template_name, {"error": exc.message}, status=exc.status)
        return render(request, self.template_name, {"invitation": invitation, "token": token})

    def post(self, request):
        token = request.POST.get("token", "")
        password = request.POST.get("password", "")
        confirm = request.POST.get("password_confirm", "")

        # Re-read the invitation so the form can be redisplayed with the email intact when
        # the password is rejected. An invalid token here is fatal, same as on GET.
        try:
            invitation = get_valid_invitation(token)
        except InvitationError as exc:
            return render(request, self.template_name, {"error": exc.message}, status=exc.status)

        ctx = {"invitation": invitation, "token": token}
        if password != confirm:
            return render(request, self.template_name, dict(ctx, form_error="The two passwords do not match."), status=400)

        try:
            user = accept_invitation(token, password)
        except InvitationError as exc:
            return render(request, self.template_name, dict(ctx, form_error=exc.message), status=400)

        # Two backends are configured, so login() needs to be told which one authenticated
        # this user; without it Django raises "You have multiple authentication backends".
        auth_login(request, user, backend="apps.accounts.backends.EmailOrUsernameModelBackend")
        return redirect("spa")


# --- Password reset -------------------------------------------------------------------
# Django's four-step flow (request -> email sent -> set new password -> done), branded to
# match the login page. The reset email's link is built from the request's own host, so it
# points at localhost in dev and at the deployed domain in production with no configuration.


@method_decorator(login_not_required, name="dispatch")
class PasswordResetView(auth_views.PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.txt"
    subject_template_name = "registration/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


@method_decorator(login_not_required, name="dispatch")
class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


@method_decorator(login_not_required, name="dispatch")
class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


@method_decorator(login_not_required, name="dispatch")
class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"
