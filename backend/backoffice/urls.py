from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AddContainersView,
    CompanyEditView,
    CompanyProfileView,
    CustomerShipmentsHistoryView,
    CustomerShipmentsView,
    DashboardStatsAPIView,
    OnboardingView,
    ShipmentGetUpdateDeleteView,
    ShipmentView,
)
from .viewsets import AssociateCompanyViewSet

router = DefaultRouter()
router.register(r"associate-company", AssociateCompanyViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("company/onboarding/", OnboardingView.as_view(), name="onboarding"),
    path("company/edit/<int:pk>/", CompanyEditView.as_view(), name="edit-company"),
    path("company/view/", CompanyProfileView.as_view(), name="company-view"),
    # ... other url patterns ...
    path("container/add/", AddContainersView.as_view(), name="add-containers"),
    path("shipments/", ShipmentView.as_view(), name="shipment-list"),
    path(
        "shipments/<int:pk>/",
        ShipmentGetUpdateDeleteView.as_view(),
        name="shipment-detail",
    ),
    path(
        "shipments/customers/",
        CustomerShipmentsView.as_view(),
        name="latest-shipments",
    ),
    path(
        "shipments/customers/<int:id>/",
        CustomerShipmentsHistoryView.as_view(),
        name="latest-shipments",
    ),
    path("dashboard-stats/", DashboardStatsAPIView.as_view(), name="dashboard-stats"),
]
