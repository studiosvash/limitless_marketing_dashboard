from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("seo/", views.seo, name="seo"),
    path("keywords/", views.keywords, name="keywords"),
    path("keywords/explore/", views.keyword_explorer_search, name="keyword_explorer_search"),
    path("keywords/save/", views.save_keywords, name="save_keywords"),
    path("keywords/saved/delete/", views.delete_saved_keyword, name="delete_saved_keyword"),
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
    path("update-site-credentials/", views.update_site_credentials, name="update_site_credentials"),
    path("export/<str:table_name>/", views.export_csv, name="export_csv"),
    path("add-site/", views.add_site, name="add_site"),
]
