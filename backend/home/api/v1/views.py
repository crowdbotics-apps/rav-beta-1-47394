import json
import logging

from backoffice.models import Company
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from google.auth.transport import requests
from google.oauth2 import id_token
from home.api.v1.serializers import (
    BackOfficeUserSerializer,
    ChangePasswordSerializer,
    ContactUsSerializer,
    DriverSerializer,
    GoogleAuthSerializer,
    GoogleSignUpSerializer,
    PasswordResetSerializer,
    ProfilePictureSerializer,
    UserForgotPasswordSerializer,
    UserSerializer,
    WarehouseUserSerializer,
)
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from services.google_outh import exchange_code_for_tokens, get_user_info_from_google
from users.models import (
    BackOfficeUser,
    Device,
    Driver,
    Notification,
    User,
    WarehouseUser,
)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response(
                    {"error": "Incorrect password!. Old password did not match"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response(
                {"success": "Password Changes Successfully"},
                status=status.HTTP_204_NO_CONTENT,
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


class ProfilePictureUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = ProfilePictureSerializer(user, data=request.data)
        if serializer.is_valid():
            # serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
        )

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ProfilePictureSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": "Profile Picture Uploaded"}, status=status.HTTP_200_OK
            )
        return Response(
            {"error": "Unable to upload Profile Picture"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ForgotPasswordView(generics.UpdateAPIView):
    serializer_class = UserForgotPasswordSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = request.data.get("email").lower()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status.HTTP_404_NOT_FOUND)

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        reset_url = f"{settings.RESET_URL}?token={token}&uid={uid}"

        message = render_to_string(
            "reset_password.html",
            {
                "user": user,
                "reset_password_url": reset_url,
            },
        )
        recipient_list = [email]
        try:
            send_mail(
                settings.FORGOT_PASSWORD["EMAIL_SUBJECT"],
                "",
                from_email=settings.FROM_EMAIL,
                recipient_list=recipient_list,
                html_message=message,
            )
        except Exception as ex:
            return Response(
                {"error": "Unable to send email - please try again"},
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"exception": str(ex)},
            )

        return Response(
            {"success": "Password Recovery email sent"}, status.HTTP_202_ACCEPTED
        )


class UserResetPasswordView(generics.CreateAPIView):
    serializer_class = PasswordResetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            try:
                uid = force_text(
                    urlsafe_base64_decode(serializer.validated_data["uid"])
                )
                print(uid)
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response(
                    {"error": "Invalid UID."}, status=status.HTTP_400_BAD_REQUEST
                )

            token_generator = PasswordResetTokenGenerator()
            print(serializer.validated_data["token"])
            if not token_generator.check_token(
                user, serializer.validated_data["token"]
            ):
                return Response(
                    {"error": "Invalid token or token has expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if user.check_password(serializer.validated_data["new_password1"]):
                return Response(
                    {"error": "New password cannot be the same as the old password."}
                )
            user.set_password(serializer.validated_data["new_password1"])
            user.save()
            return Response(
                {"success": "Password has been reset with the new password."},
                status.HTTP_202_ACCEPTED,
            )
        else:
            first_error_detail = serializer.errors["non_field_errors"][0]
            return Response(
                {"error": first_error_detail}, status=status.HTTP_400_BAD_REQUEST
            )


class GoogleLoginView(APIView):
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        platform = request.headers.get("Platform")

        if platform == "mobile":
            user_type = request.data["user_type"]
            user_info_response = get_user_info_from_google(token)

            if "error" in user_info_response:
                logging.error(
                    "Error fetching user info from Google API: %s",
                    user_info_response["error_description"],
                )
                return Response(
                    {"error": "Failed to fetch user info from Google API"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get or create user from database
            user = User.objects.filter(email=user_info_response["email"]).first()
            if user:
                if user.user_type == "backoffice":
                    return Response(
                        {"error": f"{user.user_type} is not allowed to login on web"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # User exists, authenticate and return token
                # Create or retrieve a token for the user (if using token-based authentication)
                token, created = Token.objects.get_or_create(user=user)

                if hasattr(user, "backoffice"):
                    user_data = BackOfficeUserSerializer(user.backoffice).data
                elif hasattr(user, "driver"):
                    user_data = DriverSerializer(user.driver).data

                elif hasattr(user, "warehouse"):
                    user_data = WarehouseUserSerializer(user.warehouse).data

                else:
                    user_data = UserSerializer(user).data
                    # Include the token in the response
                return Response(
                    {
                        "token": token.key,
                        "success": "User logged in successfully",
                        "user_data": user_data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                new_user = User.objects.create_user(
                    email=user_info_response["email"].lower(),
                    username=user_info_response["email"],
                    first_name=user_info_response.get("given_name", ""),
                    last_name=user_info_response.get("family_name", ""),
                    user_type=user_type,
                )

                if new_user:
                    # Create or retrieve a token for the user (if using token-based authentication)
                    token, created = Token.objects.get_or_create(user=new_user)
                    if user_type == "backoffice":
                        backoffice = BackOfficeUser.objects.create(user=new_user)
                        user_data = BackOfficeUserSerializer(backoffice).data
                    elif user_type == "driver":
                        driver = Driver.objects.create(user=new_user)
                        user_data = DriverSerializer(driver).data
                    elif user_type == "warehouse":
                        warehouse = WarehouseUser.objects.create(user=new_user)
                        user_data = WarehouseUserSerializer(warehouse).data
                    else:
                        user_data = UserSerializer(user).data
                    return Response(
                        {
                            "token": token.key,
                            "success": "User signed up and logged in successfully",
                            "user_data": user_data,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"error": "Unable to create user."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
        else:

            try:
                # Add your Google Client ID here
                tokens_response = exchange_code_for_tokens(token)

                if "error" in tokens_response:
                    logging.error(
                        "Error exchanging code for tokens: %s",
                        tokens_response["error_description"],
                    )
                    return Response(
                        {"error": "Failed to exchange code for tokens"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                access_token = tokens_response.get("access_token")
                user_info_response = get_user_info_from_google(access_token)

                if "error" in user_info_response:
                    logging.error(
                        "Error fetching user info from Google API: %s",
                        user_info_response["error_description"],
                    )
                    return Response(
                        {"error": "Failed to fetch user info from Google API"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Get or create user from database
                user = User.objects.filter(email=user_info_response["email"]).first()
                if user:
                    if (
                        not platform
                        and user.user_type == "driver"
                        or user.user_type == "warehouse"
                    ):
                        return Response(
                            {
                                "error": f"{user.user_type} is not allowed to login on web"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    # User exists, authenticate and return token
                    # Create or retrieve a token for the user (if using token-based authentication)
                    token, created = Token.objects.get_or_create(user=user)

                    # Include the token in the response
                    return Response(
                        {
                            "token": token.key,
                            "success": "User logged in successfully",
                            "user": UserSerializer(user).data,
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {"error": "User does not exist. Please sign up."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            except ValueError:
                # Invalid token
                logging.error("Invalid token")
                return Response(
                    {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
                )


class GoogleSignUpView(APIView):
    def post(self, request):
        serializer = GoogleSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        user_type = serializer.validated_data["user_type"]
        try:
            tokens_response = exchange_code_for_tokens(token)
            print(tokens_response)
            if "error" in tokens_response:
                logging.error(
                    "Error exchanging code for tokens: %s",
                    tokens_response["error_description"],
                )
                return Response(
                    {"error": "Failed to exchange code for tokens"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            access_token = tokens_response.get("access_token")
            user_info_response = get_user_info_from_google(access_token)
            if "error" in user_info_response:
                logging.error(
                    "Error fetching user info from Google API: %s",
                    user_info_response["error_description"],
                )
                return Response(
                    {"error": "Failed to fetch user info from Google API"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if the user already exists
            user = User.objects.filter(email=user_info_response["email"]).first()
            if user:
                return Response(
                    {"error": "User already exists. Please log in."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                # Create a new user
                new_user = User.objects.create_user(
                    email=user_info_response["email"].lower(),
                    username=user_info_response["email"],
                    first_name=user_info_response.get("given_name", ""),
                    last_name=user_info_response.get("family_name", ""),
                    user_type=user_type,
                )

                if new_user:
                    # Create or retrieve a token for the user (if using token-based authentication)
                    token, created = Token.objects.get_or_create(user=new_user)
                    # if user_type == "backoffice":
                    #     BackOfficeUser.objects.create(user=new_user)
                    # elif user_type == "driver":
                    #     Driver.objects.create(user=new_user)
                    # elif user_type == "warehouse":
                    #     WarehouseUser.objects.create(user=new_user)

                    if user_type == "backoffice":
                        backoffice = BackOfficeUser.objects.create(user=new_user)
                        user_data = BackOfficeUserSerializer(backoffice).data
                    elif user_type == "driver":
                        driver = Driver.objects.create(user=new_user)
                        user_data = DriverSerializer(driver).data
                    elif user_type == "warehouse":
                        warehouse = WarehouseUser.objects.create(user=new_user)
                        user_data = WarehouseUserSerializer(warehouse).data
                    else:
                        user_data = UserSerializer(user).data
                    # Include the token in the response
                    return Response(
                        {
                            "token": token.key,
                            "success": "User signed up and logged in successfully",
                            "user": UserSerializer(new_user).data,
                        },
                        status=status.HTTP_201_CREATED,
                    )
                else:
                    return Response(
                        {"error": "Authentication failed"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except ValueError:
            # Invalid token
            logging.error("Invalid token")
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class ContactUsView(APIView):
    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)

        if serializer.is_valid():
            # Extract data from the serializer
            full_name = serializer.validated_data["full_name"]
            email = serializer.validated_data["email"]
            message = serializer.validated_data["message"]

            # Send email
            email_subject = "Contact Us Form Submission"
            email_body = f"Full Name: {full_name}\nEmail: {email}\nMessage: {message}"

            try:
                send_mail(
                    email_subject,
                    email_body,
                    settings.FROM_EMAIL,  # Replace with your sender's email address
                    # Replace with your email address where you want to receive the form submissions
                    [settings.FROM_EMAIL],
                    fail_silently=False,
                )

                return Response(
                    {"success": "Form submitted successfully"},
                    status=status.HTTP_200_OK,
                )
            except Exception as e:
                # Handle email sending failure
                return Response(
                    {"error": "Failed to submit form. Please try again later."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            # Return validation errors if the data is not valid
            return Response(
                {"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        platform = request.headers.get("platform")
        if platform == "mobile":
            if hasattr(user, "backoffice"):
                user_data = BackOfficeUserSerializer(user.backoffice).data
            elif hasattr(user, "driver"):
                user_data = DriverSerializer(user.driver).data

            elif hasattr(user, "warehouse"):
                user_data = WarehouseUserSerializer(user.warehouse).data

            if platform == "mobile":
                # Prepare the custom response data
                return Response({"user_data": user_data}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"user": UserSerializer(request.user).data}, status=status.HTTP_200_OK
            )


class UserLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        device = Device.objects.filter(
            user=request.user,
        ).first()
        if device:
            device.delete()
        return Response(
            {"success": "User Logout successfully"}, status=status.HTTP_200_OK
        )


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Mark all notifications for the user as read
        Notification.objects.filter(recipient=request.user).update(read=True)
        return Response(
            {
                "success": "All notifications have been marked as read.",
            },
            status=status.HTTP_200_OK,
        )


class DeleteAllNotification(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logging.info(f"Received method: {request.method}")
        # Mark all notifications for the user as read
        Notification.objects.filter(recipient=request.user).delete()
        return Response(
            {
                "success": "All notifications have been deleted.",
            },
            status=status.HTTP_200_OK,
        )


class UserProfileUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.phone_number = request.data.get("phone_number", user.phone_number)
        user.profile_picture = request.data.get("profile_picture", user.profile_picture)
        payload_str = request.data.get("payload", "")
        if payload_str:
            try:
                user.payload = json.loads(payload_str)
            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid JSON format in payload."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # user.payload = request.data.get("payload", user.payload)
        user.save()

        if request.user.user_type == "driver":
            driver, created = Driver.objects.get_or_create(
                user=user
            )  # Ensure the driver profile exists
            # Update driver-specific fields
            driver_fields = [
                "company_name",
                "state",
                "emergency_number",
                "license_number",
                "registration_state",
                "twic_number",
                "dot_number",
                "dg_certification",
            ]
            driver_payload_str = request.data.get("driver_payload", "")
            if driver_payload_str:
                try:
                    driver.driver_payload = json.loads(driver_payload_str)
                except json.JSONDecodeError:
                    return Response(
                        {"error": "Invalid JSON format in driver payload."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            for field in driver_fields:
                setattr(driver, field, request.data.get(field, getattr(driver, field)))
            driver.save()
            user_data = DriverSerializer(user.driver).data

            return Response(
                {"success": "Profile updated successfully.", "user_data": user_data},
                status=status.HTTP_200_OK,
            )

        elif request.user.user_type == "warehouse":
            warehouse_user, _ = WarehouseUser.objects.get_or_create(user=user)
            # If you need to update fields in WarehouseUser, do it here

            # Find and update the company based on company email
            company_email = request.data.get("company_email")
            if company_email:
                company = get_object_or_404(Company, company_email=company_email)
                company_fields = [
                    "company_name",
                    "company_email",
                    "company_phone_number",
                    "address",
                    "country",
                    "city",
                    "state",
                    "zip_code",
                    "company_bio",
                ]
                company_payload_str = request.data.get("company_payload", "")
                if company_payload_str:
                    try:
                        company.company_payload = json.loads(company_payload_str)
                    except json.JSONDecodeError:
                        return Response(
                            {"error": "Invalid JSON format in company payload."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                for field in company_fields:
                    setattr(
                        company, field, request.data.get(field, getattr(company, field))
                    )
                company.save()

                # Link the warehouse user to the updated company
                warehouse_user.company = company
                warehouse_user.save()

                user_data = WarehouseUserSerializer(user.warehouse).data
                return Response(
                    {
                        "success": "Warehouse user profile updated successfully.",
                        "user_data": user_data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Company email is required for updating  data."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.user.user_type == "backoffice":
            backoffice_user, _ = BackOfficeUser.objects.get_or_create(user=user)
            # If you need to update fields in WarehouseUser, do it here

            # Find and update the company based on company email
            company_email = request.data.get("company_email")
            if company_email:
                try:
                    company = Company.objects.get(pk=backoffice_user.company_id)
                except:
                    return Response(
                        {"error": "Company not found."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                company_fields = [
                    "company_name",
                    "company_email",
                    "company_phone_number",
                    "address",
                    "country",
                    "city",
                    "state",
                    "zip_code",
                    "company_bio",
                ]
                company_payload_str = request.data.get("company_payload", "")
                if company_payload_str:
                    try:
                        company.company_payload = json.loads(company_payload_str)
                    except json.JSONDecodeError:
                        return Response(
                            {"error": "Invalid JSON format in company payload."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                for field in company_fields:
                    setattr(
                        company, field, request.data.get(field, getattr(company, field))
                    )
                company.save()

                # Link the warehouse user to the updated company
                backoffice_user.company = company
                backoffice_user.save()

                user_data = UserSerializer(user).data
                return Response(
                    {
                        "success": " user profile updated successfully.",
                        "user_data": user_data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Company email is required for updating  data."},
                    status=status.HTTP_400_BAD_REQUEST,
                )


class DeleteUserAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            # Attempt to retrieve the user and delete them
            user_id = request.user.id
            user = User.objects.get(id=user_id)
            user.delete()
            return Response(
                {"success": "User deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:

            return Response(
                {"error": "User not found."}, status=status.HTTP_404_NOT_FOUND
            )
