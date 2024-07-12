from django.urls import include, path
from home.api.v1.viewsets import (
    DeviceViewSet,
    DriverViewSet,
    FeedbackViewSet,
    LoginViewSet,
    NotificationViewSet,
    SignupViewSet,
    WarehouseViewSet,
)
from rest_framework.routers import DefaultRouter

from .views import (
    ChangePasswordView,
    ContactUsView,
    DeleteAllNotification,
    DeleteUserAPIView,
    ForgotPasswordView,
    GoogleLoginView,
    GoogleSignUpView,
    MarkNotificationReadView,
    ProfilePictureUploadView,
    UserLogoutView,
    UserProfileUpdate,
    UserProfileView,
    UserResetPasswordView,
)

router = DefaultRouter()
router.register("signup", SignupViewSet, basename="signup")
router.register("login", LoginViewSet, basename="login")
router.register(r"driver", DriverViewSet)
router.register(r"warehouse", WarehouseViewSet)
router.register(r"feedback", FeedbackViewSet)
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"devices", DeviceViewSet, basename="device")
urlpatterns = [
    path("", include(router.urls)),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
    path(
        "upload-profile-picture/",
        ProfilePictureUploadView.as_view(),
        name="upload_profile_picture",
    ),  # Add this line for change password
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/", UserResetPasswordView.as_view(), name="reset-password"),
    path("user-profile/", UserProfileView.as_view(), name="user-profile"),
    path("user/logout/", UserLogoutView.as_view(), name="user-logout"),
    path("auth/google/login/", GoogleLoginView.as_view(), name="google_auth"),
    path("auth/google/signup/", GoogleSignUpView.as_view(), name="google_signup"),
    path(
        "user-profile-update/",
        UserProfileUpdate.as_view(),
        name="user-profile-update",
    ),
    path("contact-us/", ContactUsView.as_view(), name="contact"),
    path(
        "read-all/notifications/",
        MarkNotificationReadView.as_view(),
        name="mark-notification-read",
    ),
    path(
        "delete-all/notifications/",
        DeleteAllNotification.as_view(),
        name="mark-notification-read",
    ),
    path("delete-user/", DeleteUserAPIView.as_view(), name="delete-user"),
]
