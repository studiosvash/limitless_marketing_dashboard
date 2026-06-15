"""Role-based access control for page views.

Usage:
    from apps.accounts.decorators import role_required

    @role_required("ads")
    def ads(request): ...

Founders pass everything. Other roles pass only the pages allowed in models.ROLE_PAGE_ACCESS.
Unauthenticated requests are handled upstream by LoginRequiredMiddleware (→ login page);
an authenticated user without access gets a 403 (PermissionDenied).
"""

from functools import wraps

from django.core.exceptions import PermissionDenied


def role_required(page_key: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            profile = getattr(request.user, "profile", None)
            if profile is None or not profile.can_access(page_key):
                raise PermissionDenied(
                    f"Your role does not have access to the '{page_key}' page."
                )
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
