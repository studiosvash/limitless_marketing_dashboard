from django.contrib.auth.decorators import login_not_required
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.views import APIView


@method_decorator(login_not_required, name="dispatch")
class PingView(APIView):
    """Smoke-test endpoint: proves auth + routing work before any real data endpoint exists."""

    def get(self, request):
        return Response({"ok": True})
