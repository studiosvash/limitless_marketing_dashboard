"""URL configuration.

The old Django-template dashboard (apps.dashboard.urls + apps.sync.urls, which rendered
templates/dashboard/*.html) has been removed. The SPA at /app/ is now the only frontend, and
it talks exclusively to the JSON API under /api/.

  /          -> redirects to /app/
  /login/    -> login page (the one remaining server-rendered template)
  /app/      -> the SPA (login-protected)
  /api/...   -> JSON API the SPA consumes (incl. Refresh/Sync + Keyword Explorer)
  /admin/    -> Django admin
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from apps.dashboard.spa_views import spa_index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),   # login / logout
    path('api/', include('apps.api.urls')),
    path('app/', spa_index, name='spa'),
    path('', RedirectView.as_view(pattern_name='spa', permanent=False), name='home'),
]
