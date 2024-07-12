from django.urls import path
from rest_framework.routers import DefaultRouter
from users.views import user_detail_view, user_redirect_view, user_update_view

# from .views import UserViewSet, DriverViewSet, BackOfficeUserViewSet, WarehouseUserViewSet

router = DefaultRouter()
# router.register(r'users', UserViewSet,basename='user')
# router.register(r'drivers', DriverViewSet,basename='driver')
# router.register(r'backoffice', BackOfficeUserViewSet,basename='backofficeuser')
# router.register(r'warehouse', WarehouseUserViewSet,basename='warehouseuser')


app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
urlpatterns += router.urls
