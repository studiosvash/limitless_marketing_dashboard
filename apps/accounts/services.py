"""Invitation acceptance rules, shared by the two entry points that use them.

An invite can be accepted from the emailed link (the server-rendered page in
`apps.accounts.views.AcceptInviteView`, which is what invitees actually click) or from the
SPA's JSON endpoint (`apps.api.views.AuthInviteAcceptView`). Both must enforce the same
rules — token validity, 48-hour expiry, one-time use, and username = the invited email
address — so the rules live here instead of being duplicated in, and drifting between, the
two views.

The invitee's **username is their email address**. They are invited by email, the login form
already accepts an email (see `EmailOrUsernameModelBackend`), and asking someone to invent a
username before they have ever seen the product is one more thing to forget.
"""

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import UserInvitation


class InvitationError(Exception):
    """An invitation was rejected. `status` is the HTTP code the JSON endpoint returns;
    the HTML page shows `message` and ignores it."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


def get_valid_invitation(token: str) -> UserInvitation:
    """Return the pending, unexpired invitation for `token`, or raise InvitationError."""
    token = (token or "").strip()
    if not token:
        raise InvitationError("This invitation link is missing its token.", status=404)

    invitation = UserInvitation.objects.filter(token=token).first()
    if not invitation:
        raise InvitationError("Invitation link is invalid or not found.", status=404)
    if invitation.is_accepted:
        raise InvitationError("This invitation has already been accepted. Please sign in instead.")
    if invitation.expires_at < timezone.now():
        raise InvitationError("This invitation link has expired. Please ask the owner to resend it.")
    return invitation


def accept_invitation(token: str, password: str, username: str | None = None) -> User:
    """Create the invited user with the password they chose and mark the invite accepted.

    `username` defaults to the invited email address. It stays overridable only because the
    SPA's JSON endpoint has always accepted one and its callers still send it; nothing in the
    emailed flow passes it.
    """
    invitation = get_valid_invitation(token)

    password = password or ""
    username = (username or "").strip() or invitation.email

    if User.objects.filter(email__iexact=invitation.email).exists():
        raise InvitationError("A user account with this email address already exists.")
    if User.objects.filter(username__iexact=username).exists():
        raise InvitationError("This username is already taken. Please choose another username.")

    # Django's configured validators (length, common-password, all-numeric, similarity to the
    # username/email) rather than a bare len() check, so the rule here is the same one
    # /admin and the password-reset flow enforce.
    probe = User(username=username, email=invitation.email)
    try:
        validate_password(password, user=probe)
    except ValidationError as exc:
        raise InvitationError(" ".join(exc.messages)) from exc

    with transaction.atomic():
        user = User.objects.create_user(username=username, email=invitation.email, password=password)
        user.is_active = True
        user.save(update_fields=["is_active"])

        # The post_save signal already created the profile; this sets the invited role on it.
        profile = user.profile
        profile.role = invitation.role
        profile.save(update_fields=["role"])

        invitation.is_accepted = True
        invitation.save(update_fields=["is_accepted"])

    try:
        from apps.dashboard.services.notifications_service import notify
        notify("user_added", f"{invitation.email} joined as {invitation.role}",
               severity="info")
    except Exception:
        pass  # a bell notification must never block account creation

    return user
