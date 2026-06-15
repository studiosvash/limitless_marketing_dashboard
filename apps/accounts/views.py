"""Authentication views. Thin wrappers over Django's built-in auth so we get a
branded login page while keeping Django's secure session handling.

The login view is marked `login_not_required` so it stays reachable under
LoginRequiredMiddleware (which otherwise protects every view by default).
"""

from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.utils.decorators import method_decorator


@method_decorator(login_not_required, name="dispatch")
class LoginView(auth_views.LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True
