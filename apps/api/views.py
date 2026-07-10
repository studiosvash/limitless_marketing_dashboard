from django.contrib.auth.decorators import login_not_required
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView


# login_not_required bypasses session-based LoginRequiredMiddleware (active project-wide)
# so DRF's own TokenAuthentication/IsAuthenticated run instead — without this, anonymous
# requests get a 302 to the login page rather than DRF's 401. Every future apps.api view
# needs this too.
@method_decorator(login_not_required, name="dispatch")
class PingView(APIView):
    """Smoke-test endpoint: proves auth + routing work before any real data endpoint exists."""

    def get(self, request):
        return Response({"ok": True})
