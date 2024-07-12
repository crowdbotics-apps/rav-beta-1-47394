import logging

from backoffice.permissions import IsDriverUser, IsWarehouseUser
from home.api.v1.serializers import (
    BackOfficeUserSerializer,
    DeviceSerializer,
    DriverSerializer,
    FeedbackSerializer,
    LoginAuthTokenSerializer,
    NotificationSerializer,
    SignupSerializer,
    UserSerializer,
    WarehouseUserSerializer,
)
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ErrorDetail
from rest_framework.permissions import IsAuthenticated  # Import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet
from users.models import Device, Driver, Feedback, Notification, WarehouseUser

from .serializers import DriverSerializer, WarehouseUserSerializer


class SignupViewSet(ModelViewSet):
    serializer_class = SignupSerializer
    http_method_names = ["post"]

    def create(self, request, *args, **kwargs):
        platform = request.headers.get("Platform")
        serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            user = serializer.save(request=request)

            # Create token for the new user
            token, created = Token.objects.get_or_create(user=user)

            if hasattr(user, "backoffice"):
                user_data = BackOfficeUserSerializer(user.backoffice).data
            elif hasattr(user, "driver"):
                user_data = DriverSerializer(user.driver).data

            elif hasattr(user, "warehouse"):
                user_data = WarehouseUserSerializer(user.warehouse).data

            if platform == "mobile":
                # Prepare the custom response data
                response_data = {
                    "user_data": user_data,
                    # "user": UserSerializer(
                    #     user
                    # ).data,  # Or any other serializer you wish to use for the user
                    "token": token.key,
                }

                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {
                        "token": token.key,
                        "user": UserSerializer(user).data,
                        "status_code": status.HTTP_201_CREATED,
                    }
                )
        else:
            error_messages = []

            # Iterate over the error messages
            for error in serializer.errors.values():
                # for error in field_errors:
                if "message" in error and isinstance(error["message"], ErrorDetail):
                    error_messages.append(str(error["message"]))
                else:
                    error_messages.append(error[0])

            # Join all error messages into a single string
            all_errors = ". ".join(error_messages)
            return Response({"error": all_errors}, status=status.HTTP_400_BAD_REQUEST)


class LoginViewSet(ViewSet):
    """Based on rest_framework.authtoken.views.ObtainAuthToken"""

    serializer_class = LoginAuthTokenSerializer

    def create(self, request):
        platform = request.headers.get("Platform")
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            if not platform and (
                user.user_type == "driver" or user.user_type == "warehouse"
            ):
                return Response(
                    {"error": f"{user.user_type} is not allowed to login on web"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if platform == "mobile" and user.user_type == "backoffice":
                return Response(
                    {"error": f"{user.user_type} is not allowed to login on Mobile"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # serializer.is_valid(raise_exception=True)
            token, created = Token.objects.get_or_create(user=user)

            if hasattr(user, "backoffice"):
                user_data = BackOfficeUserSerializer(user.backoffice).data
            elif hasattr(user, "driver"):
                user_data = DriverSerializer(user.driver).data

            elif hasattr(user, "warehouse"):
                user_data = WarehouseUserSerializer(user.warehouse).data

            else:
                user_data = UserSerializer(user).data
            # user_serializer = UserSerializer(user)
            if platform == "mobile":
                deleted = Token.objects.filter(user=user).delete()
                logging.warning(f"Token deleted {deleted}")
                # Then, create a new token for the user
                token = Token.objects.create(user=user)
                return Response(
                    {
                        "token": token.key,
                        "user_data": user_data,
                        # "user": UserSerializer(user).data,
                        "status_code": status.HTTP_201_CREATED,
                    }
                )
            else:
                return Response(
                    {
                        "token": token.key,
                        "user_data": user_data,
                        "user": UserSerializer(user).data,
                        "status_code": status.HTTP_201_CREATED,
                    }
                )
        else:
            error_messages = []

            # Iterate over the error messages
            for error in serializer.errors.values():
                # for error in field_errors:

                error_messages.append(error[0])
                # error_messages.append(error.title())

            # Join all error messages into a single string
            all_errors = ". ".join(error_messages)
            return Response({"error": all_errors}, status=status.HTTP_400_BAD_REQUEST)


class DriverViewSet(ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    permission_classes = [IsDriverUser]
    pagination_class = None


class WarehouseViewSet(ModelViewSet):
    queryset = WarehouseUser.objects.all()
    serializer_class = WarehouseUserSerializer
    permission_classes = [IsWarehouseUser]
    pagination_class = None


class FeedbackViewSet(ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def perform_create(self, serializer):
        serializer.save(email=self.request.user.email)


class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]  # En

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user).order_by(
            "-created_at"
        )
        is_read = self.request.query_params.get("is_read")

        if is_read is not None:
            is_read_value = is_read.lower() in ["true", "1", "t"]
            queryset = queryset.filter(read=is_read_value)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Here we calculate the count of unread notifications
        unread_count = queryset.filter(read=False).count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(
                {"unread_count": unread_count, "notifications": serializer.data},
            )

        serializer = self.get_serializer(queryset, many=True)
        # Customize the response to include unread_count
        return Response(
            {"unread_count": unread_count, "notifications": serializer.data},
            status=status.HTTP_200_OK,
        )


class DeviceViewSet(ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        existing_device = Device.objects.filter(user=self.request.user).first()

        if existing_device:
            # If a device exists, update the existing device's registration_id
            # with the new one from the request
            existing_device.registration_id = serializer.validated_data[
                "registration_id"
            ]
            existing_device.save()
        else:
            # If no device exists for this user, create a new device instance
            serializer.save(user=self.request.user)
