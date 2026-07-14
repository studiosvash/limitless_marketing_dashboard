"""URL configuration.

The old Django-template dashboard (apps.dashboard.urls + apps.sync.urls, which rendered
templates/dashboard/*.html) has been removed. The SPA at /app/ is now the only frontend, and
it talks exclusively to the JSON API under /api/.

  /          -> the SPA (login-protected; logged-out visitors get the login page)
  /login/    -> login page (the one remaining server-rendered template)
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
    # The SPA used to live at /app/; keep that working as a redirect so old links/bookmarks
    # don't 404.
    path('app/', RedirectView.as_view(pattern_name='spa', permanent=False)),
    # The SPA is served at the site root -- visiting "/" is the app (and, when logged out,
    # sends you to the login page and back again, like the old dashboard did).
    path('', spa_index, name='spa'),
]
