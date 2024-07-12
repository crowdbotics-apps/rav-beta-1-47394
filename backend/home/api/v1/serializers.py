import logging

from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.forms import ResetPasswordForm
from allauth.account.utils import setup_user_email
from allauth.utils import email_address_exists, generate_unique_username
from backoffice.models import Company, Shipment
from dj_rest_auth.serializers import PasswordResetSerializer
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, password_validation

# from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response
from users.models import (
    BackOfficeUser,
    Device,
    Driver,
    Feedback,
    Notification,
    WarehouseUser,
)
from utils.aws import generate_signed_url
from utils.response import error_response, success_response
from utils.validation import validate_password

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    user_type = serializers.ChoiceField(choices=["backoffice", "driver", "warehouse"])
    payload = serializers.JSONField(required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "password",
            "user_type",
            "is_onboarded",
            "payload",
        )
        extra_kwargs = {
            "password": {"write_only": True, "style": {"input_type": "password"}},
            "email": {
                "required": True,
                "allow_blank": False,
            },
        }

    def _get_request(self):
        request = self.context.get("request")
        if (
            request
            and not isinstance(request, HttpRequest)
            and hasattr(request, "_request")
        ):
            request = request._request
        return request

    def validate_password(self, value):
        """
        Validate the password field.
        """

        error_message = validate_password(value)
        if error_message:
            raise serializers.ValidationError(error_message)
        return value

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    {
                        "message": "A user is already registered with this e-mail address.",
                        "status_code": status.HTTP_400_BAD_REQUEST,
                    }
                )
        return email

    def create(self, validated_data):
        user_type = validated_data.pop("user_type")
        logging.warning("------------------------------------------")
        logging.warning(validated_data)
        user = User(
            email=validated_data.get("email").lower(),
            first_name=validated_data.get("first_name"),
            last_name=validated_data.get("last_name"),
            phone_number=validated_data.get("phone_number"),
            username=generate_unique_username(
                [validated_data.get("name"), validated_data.get("email"), "user"]
            ),
            user_type=user_type,
            payload=validated_data.get("payload"),
        )
        user.set_password(validated_data.get("password"))

        if user_type == "backoffice":
            user.save()
            BackOfficeUser.objects.create(user=user)
        elif user_type == "driver":
            user.save()
            Driver.objects.create(user=user)

        elif user_type == "warehouse":
            user.save()
            WarehouseUser.objects.create(user=user)

        request = self._get_request()
        setup_user_email(request, user, [])
        return user


class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    payload = serializers.JSONField(required=False)

    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "user_type",
            "is_onboarded",
            "profile_picture",
            "payload",
        )

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            # Extract the object key from the URL
            # object_key = obj.profile_picture.url.split('/')[-1]
            object_key = obj.profile_picture.name
            logging.warning(obj)
            logging.warning("+++++++++++++++++++++++++++++++++++++++++")
            object_key = f"media/{object_key}"
            logging.warning(object_key)

            # Call your generate_signed_url function
            signed_url = generate_signed_url(
                bucket_name=settings.AWS_STORAGE_BUCKET_NAME,  # Replace with your S3 bucket name
                object_key=object_key,
                access_key_id=settings.AWS_ACCESS_KEY_ID,  # Replace with your access key id
                secret_access_key=settings.AWS_SECRET_ACCESS_KEY,  # Replace with your secret access key
                region_name=settings.AWS_STORAGE_REGION,  # Replace with your
            )

            return signed_url
        else:
            return None


class PasswordSerializer(PasswordResetSerializer):
    """Custom serializer for rest_auth to solve reset password error"""

    password_reset_form_class = ResetPasswordForm


class BackOfficeUserSerializer(serializers.ModelSerializer):
    # Assuming you have specific fields for BackOfficeUser
    class Meta:
        model = BackOfficeUser
        fields = "__all__"


class DriverSerializer(serializers.ModelSerializer):
    # Assuming you have specific fields for Driver
    user = UserSerializer(read_only=True)  # Add this line
    driver_payload = serializers.JSONField(required=False)

    class Meta:
        model = Driver
        fields = "__all__"


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class WarehouseUserSerializer(serializers.ModelSerializer):
    # Assuming you have specific fields for WarehouseUser
    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)

    class Meta:
        model = WarehouseUser
        fields = "__all__"


class LoginAuthTokenSerializer(serializers.ModelSerializer):
    email = serializers.CharField(label="Email")

    class Meta:
        model = User
        fields = ("email", "password")

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(
                request=self.context.get("request"), username=email, password=password
            )
            if not user:
                msg = _("Unable to log in with provided credentials.")
                raise serializers.ValidationError(msg, code="authorization")
        else:
            msg = _('Must include "email" and "password".')
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


# The `ChangePasswordSerializer` class is a serializer in Python that validates and handles the change
# password functionality, ensuring that the new password matches the confirmation password.
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value

    def validate(self, data):
        if data["new_password"] != data["confirm_new_password"]:
            raise serializers.ValidationError(
                {
                    "message": "Password Didn't match.",
                }
            )
        return data


class ProfilePictureSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["profile_picture"]

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            # Extract the object key from the URL
            # object_key = obj.profile_picture.url.split('/')[-1]
            object_key = obj.profile_picture.name
            logging.warning(obj)
            logging.warning("+++++++++++++++++++++++++++++++++++++++++")
            object_key = f"media/{object_key}"
            logging.warning(object_key)

            # Call your generate_signed_url function
            signed_url = generate_signed_url(
                bucket_name=settings.AWS_STORAGE_BUCKET_NAME,  # Replace with your S3 bucket name
                object_key=object_key,
                access_key_id=settings.AWS_ACCESS_KEY_ID,  # Replace with your access key id
                secret_access_key=settings.AWS_SECRET_ACCESS_KEY,  # Replace with your secret access key
                region_name=settings.AWS_STORAGE_REGION,  # Replace with your
            )

            return signed_url
        else:
            return None


class UserForgotPasswordSerializer(serializers.Serializer):
    email = serializers.CharField()


class PasswordResetSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)

    def validate(self, data):
        error_message = validate_password(data["new_password1"])
        print(error_message)

        if error_message:
            raise serializers.ValidationError(error_message)
        if data["new_password1"] != data["new_password2"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()


class GoogleSignUpSerializer(serializers.Serializer):
    token = serializers.CharField()
    user_type = serializers.CharField()


# The ContactUsSerializer class is a serializer in Python that handles the serialization and
# deserialization of contact form data.
class ContactUsSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    email = serializers.EmailField()
    message = serializers.CharField()


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ["id", "subject", "message", "email"]
        read_only_fields = ["email"]  # Make the email field read-only


class NotificationSerializer(serializers.ModelSerializer):
    shipment_id = serializers.PrimaryKeyRelatedField(
        source="shipment",
        queryset=Shipment.objects.all(),
        allow_null=True,  # If your ForeignKey allows null
        required=False,  # If you want to make this field not required for creation/updation
    )

    class Meta:
        model = Notification
        fields = (
            "id",
            "recipient",
            "title",
            "type",
            "message",
            "read",
            "created_at",
            "shipment_id",
            "data",
        )


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = "__all__"
