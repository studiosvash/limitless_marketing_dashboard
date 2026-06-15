from django.urls import path
from . import views

app_name = "sync"

urlpatterns = [
    path("sync/all/",             views.sync_all_view,    name="all"),
    path("sync/page/<str:page>/", views.sync_page_view,   name="page"),
    path("sync/status/",          views.sync_status_view, name="status"),
]
