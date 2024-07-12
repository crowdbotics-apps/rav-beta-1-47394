import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

# def home(request):
#     packages = [
#         {
#             "name": "django-allauth",
#             "url": "https://pypi.org/project/django-allauth/0.38.0/",
#         },
#         {
#             "name": "django-bootstrap4",
#             "url": "https://pypi.org/project/django-bootstrap4/0.0.7/",
#         },
#         {
#             "name": "djangorestframework",
#             "url": "https://pypi.org/project/djangorestframework/3.9.0/",
#         },
#     ]
#     context = {"packages": packages}
#     return render(request, "home/index.html", context)


def serve_assetlinks(request):
    static_dir = settings.STATICFILES_DIRS[0]
    assetlinks_path = os.path.join(static_dir, ".well-known/assetlinks.json")
    with open(assetlinks_path, "r") as f:
        assetlinks_content = f.read()
    return HttpResponse(assetlinks_content, content_type="application/json")


def serve_apple_app_site_association(request):
    static_dir = settings.STATICFILES_DIRS[0]
    apple_app_site_association_path = os.path.join(
        static_dir, ".well-known/apple-app-site-association"
    )
    with open(apple_app_site_association_path, "r") as f:
        apple_app_site_association_content = f.read()
    return HttpResponse(
        apple_app_site_association_content, content_type="application/json"
    )
