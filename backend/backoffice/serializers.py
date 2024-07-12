# pylint: disable=E1101
import logging

from core.enums import ShipmentStatus
from django.conf import settings
from home.api.v1.serializers import (
    DriverSerializer,
    UserSerializer,
    WarehouseUserSerializer,
)
from rest_framework import serializers, status
from users.models import WarehouseUser
from utils.aws import generate_signed_url

from .models import AssociateCompany, Company, Container, Shipment


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class ContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        fields = "__all__"


class OnboardingSerializer(serializers.Serializer):
    # Company fields
    company_name = serializers.CharField(max_length=255, required=False)
    company_email = serializers.EmailField(required=False)
    company_phone_number = serializers.CharField(max_length=20, required=False)
    address = serializers.CharField(required=False)
    country = serializers.CharField(max_length=100, required=False)
    city = serializers.CharField(max_length=100, required=False)
    state = serializers.CharField(max_length=100, required=False)
    zip_code = serializers.CharField(max_length=20, required=False)
    company_bio = serializers.CharField(required=False)
    # user detail
    profile_picture = serializers.ImageField(required=False)

    emergency_number = serializers.CharField(required=False)
    license_number = serializers.CharField(required=False)
    registration_state = serializers.CharField(required=False)
    twic_number = serializers.CharField(required=False)
    dot_number = serializers.CharField(required=False)
    dg_certification = serializers.CharField(required=False)
    company_payload = serializers.JSONField(required=False)
    driver_payload = serializers.JSONField(required=False)
    phone_number = serializers.CharField(required=False)
    payload = serializers.JSONField(required=False)

    def validate(self, attrs):
        # user = self.context['request'].user
        # if user.user_type != 'backoffice' or user.user_type != 'warehouse':
        #     raise serializers.ValidationError({
        #         "message": f"Only {user.user_type} users are allowed to create company",
        #         "status_code": status.HTTP_400_BAD_REQUEST,
        #     })
        if attrs.get("company_email") is not None:
            if Company.objects.filter(
                company_email=attrs.get("company_email")
            ).exists():
                raise serializers.ValidationError(
                    {
                        "message": "A company is already registered with this email address.",
                        "status_code": status.HTTP_400_BAD_REQUEST,
                    }
                )

        return attrs

    def create(self, validated_data):
        # Create the company
        user = self.context["request"].user
        phone_number = validated_data.get("phone_number")
        payload = validated_data.get("payload")
        if phone_number:
            user.phone_number = phone_number
            user.save()
        if payload:
            user.payload = payload
            user.save()
        if user.user_type == "driver":
            driver = user.driver
            driver.emergency_number = validated_data.get("emergency_number")
            driver.company_name = validated_data.get("company_name")
            driver.state = validated_data.get("state")
            driver.license_number = validated_data.get("license_number")
            driver.registration_state = validated_data.get("registration_state")
            driver.twic_number = validated_data.get("twic_number")
            driver.dot_number = validated_data.get("dot_number")
            driver.dg_certification = validated_data.get("dg_certification")
            driver.driver_payload = validated_data.get("driver_payload")
            driver.save()
            profile_picture = validated_data.get("profile_picture")
            if profile_picture:
                print("++++++++++++++++++++++++++++++++++++++++++++++++")
                print(profile_picture)
                user.profile_picture = profile_picture
                user.save()
            user.is_onboarded = True
            user.save()
            return user
        else:
            company_field_names = [
                "company_name",
                "company_email",
                "company_phone_number",
                "company_bio",
                "address",
                "country",
                "city",
                "state",
                "zip_code",
                "company_payload",
            ]
            company_data = {
                field: validated_data[field]
                for field in company_field_names
                if field in validated_data
            }
            company = Company.objects.create(**company_data)

            # user = self.context["request"].user

            # Update the backoffice user
            # backoffice_user_email = validated_data.get('backoffice_user_email')
            # backoffice_user = BackOfficeUser.objects.get(
            #     user__email=backoffice_user_email)
            print("+++++++++++++++++++++++++++++")
            print(user)

            if user.user_type == "backoffice":
                backoffice_user = user.backoffice
                backoffice_user.company = company
                backoffice_user.save()
            if user.user_type == "warehouse":
                warehouse_user = user.warehouse
                warehouse_user.company = company
                warehouse_user.save()

            # user_email = validated_data.get('backoffice_user_email')
            # user = User.objects.get(email=backoffice_user_email)

            profile_picture = validated_data.get("profile_picture")
            if profile_picture:
                print("++++++++++++++++++++++++++++++++++++++++++++++++")
                print(profile_picture)
                user.profile_picture = profile_picture
                user.save()
            user.is_onboarded = True
            user.save()

            return company


class AssociateCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociateCompany
        fields = "__all__"


class ShipmentContainersSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        choices=[(status.value, status.name) for status in ShipmentStatus]
    )

    class Meta:
        model = Shipment
        fields = "__all__"


class ShipmentSerializer(serializers.ModelSerializer):
    container = ContainerSerializer()
    assigned_date = serializers.DateField(
        format="%Y/%m/%d", required=False, allow_null=True
    )
    # If there are other foreign key relations like 'customer' or 'driver', you would serialize them similarly.
    customer = AssociateCompanySerializer(
        required=False,
        allow_null=True,
    )
    driver = DriverSerializer(required=False, allow_null=True)
    warehouse = WarehouseUserSerializer(required=False, allow_null=True)

    delivery_order_file = serializers.FileField(allow_null=True, required=False)
    bill_of_landing_file = serializers.FileField(allow_null=True, required=False)
    proof_of_delivery_file = serializers.FileField(allow_null=True, required=False)
    status = serializers.ChoiceField(
        choices=[(status.value, status.name) for status in ShipmentStatus]
    )

    class Meta:
        model = Shipment
        fields = "__all__"

    def get_delivery_order_file(self, obj):
        if obj.delivery_order_file:
            # Extract the object key from the URL
            # object_key = obj.profile_picture.url.split('/')[-1]
            object_key = obj.delivery_order_file.name
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

    def get_bill_of_landing_file(self, obj):
        if obj.bill_of_landing_file:
            # Extract the object key from the URL
            # object_key = obj.profile_picture.url.split('/')[-1]
            object_key = obj.bill_of_landing_file.name
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

    def get_proof_of_delivery_file(self, obj):
        if obj.proof_of_delivery_file:
            # Extract the object key from the URL
            # object_key = obj.profile_picture.url.split('/')[-1]
            object_key = obj.proof_of_delivery_file.name
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

    def to_representation(self, instance):
        """Modify the representation of certain fields."""
        representation = super().to_representation(instance)
        representation["delivery_order_file"] = self.get_delivery_order_file(instance)
        representation["bill_of_landing_file"] = self.get_bill_of_landing_file(instance)
        representation["proof_of_delivery_file"] = self.get_proof_of_delivery_file(
            instance
        )
        return representation


class ShipmentUpdateSerializer(serializers.ModelSerializer):
    container = ContainerSerializer()
    status = serializers.ChoiceField(
        choices=[(status.value, status.name) for status in ShipmentStatus]
    )
    delivery_order_file = serializers.FileField(allow_null=True, required=False)
    bill_of_landing_file = serializers.FileField(allow_null=True, required=False)

    class Meta:
        model = Shipment
        fields = "__all__"

    def update(self, instance, validated_data):
        container_data = validated_data.pop("container", None)
        container_serializer = self.fields["container"]

        # Update the Container instance if container data is provided
        if container_data is not None:
            container_instance = instance.container
            container_serializer.update(container_instance, container_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class CustomerWarehouseSerializer(serializers.ModelSerializer):
    latest_shipment = ShipmentUpdateSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)

    type = serializers.SerializerMethodField()

    class Meta:
        model = WarehouseUser
        fields = "__all__"  # Adjust as necessary plus the type field

    def get_type(self, obj):
        return "Warehouse"


class CustomerCompanySerializer(serializers.ModelSerializer):
    latest_shipment = ShipmentUpdateSerializer(read_only=True)
    type = serializers.SerializerMethodField()

    class Meta:
        model = AssociateCompany
        fields = "__all__"  # Adjust as necessary plus the type field

    def get_type(self, obj):
        return "Company"


class ShipmentSerializerMobileView(serializers.ModelSerializer):
    container = ContainerSerializer()
    # If there are other foreign key relations like 'customer' or 'driver', you would serialize them similarly.
    # customer = AssociateCompanySerializer(
    #     required=False,
    #     allow_null=True,
    # )
    driver = DriverSerializer(required=False, allow_null=True)
    warehouse = WarehouseUserSerializer(required=False, allow_null=True)

    delivery_order_file = serializers.FileField(allow_null=True, required=False)
    bill_of_landing_file = serializers.FileField(allow_null=True, required=False)
    proof_of_delivery_file = serializers.FileField(allow_null=True, required=False)
    status = serializers.ChoiceField(
        choices=[(status.value, status.name) for status in ShipmentStatus]
    )

    class Meta:
        model = Shipment
        fields = (
            "id",
            "container",
            "assigned_date",
            "delivery_order_file",
            "bill_of_landing_file",
            "proof_of_delivery_file",
            "status",
            "pickup_location",
            "delivery_location",
            "return_location",
            "return_time",
            "pickup_time",
            "return_day",
            "pickedup_date",
            "delivery_date",
            "delivery_from",
            "delivery_to",
            "warehouse",
            "driver",
        )

    def get_delivery_order_file(self, obj):
        if obj.delivery_order_file:
            # Extract the object key from the URL
            # object_key = obj.profile_picture.url.split('/')[-1]
            object_key = obj.delivery_order_file.name
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

    def get_bill_of_landing_file(self, obj):
        if obj.bill_of_landing_file:
            # Extract the object key from the URL
            # object_key = obj.profile_picture.url.split('/')[-1]
            object_key = obj.bill_of_landing_file.name
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

    def get_proof_of_delivery_file(self, obj):
        if obj.proof_of_delivery_file:
            # Extract the object key from the URL
            # object_key = obj.profile_picture.url.split('/')[-1]
            object_key = obj.proof_of_delivery_file.name
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

    def to_representation(self, instance):
        """Modify the representation of certain fields."""
        representation = super().to_representation(instance)
        representation["delivery_order_file"] = self.get_delivery_order_file(instance)
        representation["bill_of_landing_file"] = self.get_bill_of_landing_file(instance)
        representation["proof_of_delivery_file"] = self.get_proof_of_delivery_file(
            instance
        )
        return representation


class DashboardStatsSerializer(serializers.Serializer):
    today_shipment = serializers.IntegerField()
    total_shipment = serializers.IntegerField()
    total_driver = serializers.IntegerField()
    associate_company = serializers.IntegerField()
    shipment_history = serializers.IntegerField()
