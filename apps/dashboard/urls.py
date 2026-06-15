from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("seo/", views.seo, name="seo"),
    path("keywords/", views.keywords, name="keywords"),
    path("positioning/", views.positioning, name="positioning"),
    path("alerts/", views.alerts, name="alerts"),
    path("settings/", views.settings, name="settings"),
    path("pages/", views.pages, name="pages"),
    path("pages/detail/", views.page_detail, name="page_detail"),
    path("backlinks/", views.backlinks, name="backlinks"),
    path("ads/", views.ads, name="ads"),
    path("alerts/acknowledge/<int:anomaly_id>/", views.acknowledge_anomaly, name="acknowledge_anomaly"),
    path("set-period/", views.set_period, name="set_period"),
    path("set-site/", views.set_site, name="set_site"),
    path("set-competitors/", views.set_competitors, name="set_competitors"),
    path("export/<str:table_name>/", views.export_csv, name="export_csv"),
]
