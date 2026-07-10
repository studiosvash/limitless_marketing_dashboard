from django.contrib.auth.decorators import login_not_required
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from pipeline.services.site_service import add_site, list_sites
from pipeline.utils.db_connection import get_session
from pipeline.db.schema import Site

from .serializers import ProjectCreateSerializer, ProjectSerializer


# login_not_required bypasses session-based LoginRequiredMiddleware (active project-wide)
# so DRF's own TokenAuthentication/IsAuthenticated run instead — without this, anonymous
# requests get a 302 to the login page rather than DRF's 401. Every future apps.api view
# needs this too.
@method_decorator(login_not_required, name="dispatch")
class PingView(APIView):
    """Smoke-test endpoint: proves auth + routing work before any real data endpoint exists."""

    def get(self, request):
        return Response({"ok": True})


@method_decorator(login_not_required, name="dispatch")
class ProjectListCreateView(APIView):
    def get(self, request):
        sites = list_sites(active_only=True)
        return Response(ProjectSerializer(sites, many=True).data)

    def post(self, request):
        payload = ProjectCreateSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        site_url = data["domain"].strip()
        new_id = add_site(
            site_url=site_url,
            site_name=data.get("name") or None,
            vertical=data.get("vertical") or None,
            location=data.get("location") or "United States",
        )
        with get_session() as session:
            site = session.get(Site, new_id)
            body = ProjectSerializer(site).data
        return Response(body, status=status.HTTP_201_CREATED)
