from django.urls import path

from .views import serve_apple_app_site_association, serve_assetlinks

urlpatterns = [
    # path("", home, name="home"),
    path(".well-known/assetlinks.json", serve_assetlinks, name="serve_assetlinks"),
    path(
        ".well-known/apple-app-site-association",
        serve_apple_app_site_association,
        name="serve_apple_app_site_association",
    ),
]
