# pylint: disable=E1101
import io
import logging
from datetime import datetime, timedelta

from core.enums import ShipmentStatus
from dateutil.parser import parse  # To help with parsing the datetime strings
from dateutil.relativedelta import relativedelta  # For handling months and years
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.http import QueryDict  # Import QueryDict
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from home.api.v1.serializers import (
    BackOfficeUserSerializer,
    DriverSerializer,
    UserSerializer,
    WarehouseUserSerializer,
)
from reportlab.pdfgen import canvas

# Create your views here.
from rest_framework import status, viewsets
from rest_framework.exceptions import ErrorDetail
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from services.notification import create_and_send_notification, send_push_notification
from users.models import BackOfficeUser, Driver, Notification, WarehouseUser
from utils.generate_pdf import generate_shipment_pdf

from .models import AssociateCompany, Company, Shipment
from .permissions import IsBackofficeUser
from .serializers import (
    AssociateCompanySerializer,
    CompanySerializer,
    ContainerSerializer,
    CustomerCompanySerializer,
    CustomerWarehouseSerializer,
    DashboardStatsSerializer,
    OnboardingSerializer,
    ShipmentContainersSerializer,
    ShipmentSerializer,
    ShipmentSerializerMobileView,
    ShipmentUpdateSerializer,
)


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        platform = request.headers.get("Platform")
        serializer = OnboardingSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            # company = serializer.save()
            serializer.save()
            if platform == "mobile":
                if hasattr(request.user, "backoffice"):
                    user_data = BackOfficeUserSerializer(request.user.backoffice).data
                elif hasattr(request.user, "driver"):
                    user_data = DriverSerializer(request.user.driver).data

                elif hasattr(request.user, "warehouse"):
                    user_data = WarehouseUserSerializer(request.user.warehouse).data

                create_and_send_notification(
                    recipient=request.user,
                    title="Welcome",
                    message="Welcome to the Platform",
                    status="welcome",
                    shipment_id=None,
                )
                return Response(
                    {
                        # "company": company.id,
                        "user_data": user_data,
                        "success": "Created successfully",
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                return Response(
                    {
                        # "company": company.id,
                        "user": UserSerializer(request.user).data,
                        "success": "Created successfully",
                    },
                    status=status.HTTP_201_CREATED,
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


class CompanyEditView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk, format=None):
        try:
            company = Company.objects.get(pk=pk)
        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanySerializer(company, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CompanyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.user_type == "backoffice":
            company_data = user.backoffice.company
            serializer = CompanySerializer(company_data)
        elif user.user_type == "warehouse":
            company_data = user.warehouse.company
            serializer = CompanySerializer(company_data)
        else:
            return Response(
                {"error": "User is not a backoffice user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_200_OK)


class AddContainersView(APIView):
    permission_classes = [IsBackofficeUser]

    def post(self, request, *args, **kwargs):
        container_data = request.data.get("containers")

        if not container_data or len(container_data) > 2:
            return Response(
                {"error": "Invalid data. Provide a list of up to 2 containers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_containers = []
        with transaction.atomic():
            for container_info in container_data:
                container_serializer = ContainerSerializer(data=container_info)
                if container_serializer.is_valid():
                    created_container = container_serializer.save()
                    created_containers.append(created_container)
                else:
                    return Response(
                        container_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

            shipment_data = []
            for container in created_containers:
                shipment_instance_data = {
                    # This assumes your Shipment model's 'container' field can accept a container ID
                    "container": container.id,
                    "status": ShipmentStatus.CONTAINER_QUEUED.value,
                    "created_by": request.user.id,
                    # Include other shipment data here
                }
                shipment_data.append(shipment_instance_data)

            shipment_serializer = ShipmentContainersSerializer(
                data=shipment_data,
                many=True,
            )
            if shipment_serializer.is_valid():
                shipment_serializer.save()
                return Response(
                    {"success": "Containers and Shipments created successfully"},
                    status=status.HTTP_201_CREATED,
                )
            else:
                # If there's a validation error with creating shipments, it will be caught here
                return Response(
                    shipment_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )


class ShipmentPagination(PageNumberPagination):
    page_size = 10  #


class ShipmentView(GenericAPIView):
    serializer_class = ShipmentSerializer
    pagination_class = ShipmentPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status"]
    search_fields = ["container__container_number"]
    # You can adjust the ordering fields as needed
    ordering_fields = ["created_at"]
    ordering = ["created_at"]

    def get_queryset(self):
        # Define your custom queryset based on your model relationships
        queryset = Shipment.objects.filter(is_deleted=False)

        if self.request.user.user_type == "driver":
            try:
                driver = Driver.objects.get(user=self.request.user)

                queryset = queryset.filter(driver_id=driver)
            except Driver.DoesNotExist:
                # If the driver does not exist, return an empty queryset.
                queryset = Shipment.objects.none()
        if self.request.user.user_type == "warehouse":
            try:
                warehouse = WarehouseUser.objects.get(user=self.request.user)

                queryset = queryset.filter(warehouse_id=warehouse)
            except WarehouseUser.DoesNotExist:
                # If the driver does not exist, return an empty queryset.
                queryset = Shipment.objects.none()
        if self.request.user.user_type == "backoffice":
            queryset = queryset.filter(created_by=self.request.user)

        timeframe = self.request.query_params.get("timeframe")
        # now = timezone.now().date()
        history = False
        now = datetime.now()
        if timeframe == "today":
            start_date = now.date()
            end_date = now.date()
        elif timeframe == "tomorrow":
            start_date = (now + timedelta(days=1)).date()
            end_date = (now + timedelta(days=1)).date()
        elif timeframe == "this_week":
            start_date = (now - timedelta(days=now.weekday())).date()
            end_date = start_date + timedelta(days=6)
        elif timeframe == "past_day":
            start_date = (now - timedelta(days=1)).date()
            end_date = now.date()
            history = True
        elif timeframe == "past_week":
            start_date = (now - timedelta(weeks=1)).date()
            end_date = (now - timedelta(days=1)).date()  # Setting end_date to yesterday
            history = True
        elif timeframe == "past_month":
            start_date = (now - relativedelta(months=1)).date()
            end_date = (now - timedelta(days=1)).date()  # Setting end_date to yesterday
            history = True
        elif timeframe == "past_6_months":
            start_date = (now - relativedelta(months=6)).date()
            end_date = (now - timedelta(days=1)).date()  # Setting end_date to yesterday

            history = True

        elif timeframe == "past_year":
            start_date = (now - relativedelta(years=1)).date()
            end_date = (now - timedelta(days=1)).date()  # Setting end_date to yesterday
            history = True
        else:
            start_date = None
            end_date = None

        # if history and start_date and end_date:
        #     queryset = queryset.filter(
        #         created_at__date__gte=start_date, created_at__date__lte=end_date
        #     )
        if start_date and end_date:
            queryset = queryset.filter(
                assigned_date__gte=start_date, assigned_date__lte=end_date
            )
        elif start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        return queryset

    def apply_custom_filters(self, queryset, query_params):
        # Translate enum names to values if 'status' is in the query params
        status_param = query_params.get("status")
        if status_param:
            #     try:
            #         status_enum = ShipmentStatus[status_param]
            #         status_value = status_enum.value
            #         queryset = queryset.filter(status=status_value)
            #     except KeyError:
            #         raise Http404(_("Invalid status value."))
            # return queryset
            # Split status_param into a list, or make it a list if it's a single value
            status_list = (
                status_param.split(",") if "," in status_param else [status_param]
            )

            # Translate enum names to values and prepare ordering
            status_values = []
            ordering_case = []
            for index, status_name in enumerate(status_list):
                try:
                    status_name = (
                        status_name.strip()
                    )  # Remove any leading/trailing whitespace
                    status_enum = ShipmentStatus[status_name]
                    status_values.append(status_enum.value)
                    # Add ordering case
                    ordering_case.append(
                        When(status=status_enum.value, then=Value(index))
                    )
                except KeyError:
                    raise Http404(_("Invalid status value."))

            # Filter queryset based on the list of status values
            queryset = queryset.filter(status__in=status_values)

            # Annotate queryset with custom order and apply ordering
            custom_order = Case(*ordering_case, output_field=IntegerField())
            queryset = queryset.annotate(custom_sort=custom_order).order_by(
                "custom_sort"
            )

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        platform = request.headers.get("Platform")
        search_param = request.query_params.get("search")
        if search_param:
            queryset = queryset.filter(
                container__container_number__icontains=search_param
            )

        # Create a new QueryDict with the updated parameters
        updated_query_params = QueryDict(request.META["QUERY_STRING"], mutable=True)
        # Apply custom filters based on the updated QueryDict
        queryset = queryset.order_by("-updated_at")

        queryset = self.apply_custom_filters(queryset, updated_query_params)
        # Paginate the queryset

        page = self.paginate_queryset(queryset)

        if platform == "mobile":
            serializer = ShipmentSerializerMobileView(page, many=True)
            return self.get_paginated_response(serializer.data)
        if page is not None:
            serializer = ShipmentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ShipmentSerializer(queryset, many=True)
        return Response(serializer.data)


class ShipmentGetUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self, pk):
        try:
            return Shipment.objects.select_related("container").get(
                pk=pk, is_deleted=False
            )
        # return Shipment.objects.get(pk=pk, is_deleted=False)
        except Shipment.DoesNotExist:
            return Response(
                {"error": "Shipment Does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, pk, format=None):
        platform = request.headers.get("Platform")
        shipment = self.get_object(pk)
        if not shipment:
            return Response(
                {"error": "Shipment Does not exist"}, status=status.HTTP_404_NOT_FOUND
            )
        if platform == "mobile":
            serializer = ShipmentSerializerMobileView(shipment)
            return Response(serializer.data)
        serializer = ShipmentSerializer(shipment)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        current_user_type = request.user.user_type
        logging.info("In Shipment PUT request")
        logging.info(request)

        platform = request.headers.get("Platform")
        shipment = self.get_object(pk)
        logging.warning("Current Shipment Status")
        logging.warning(shipment.status)
        # Initialize a dictionary to hold the reformatted data
        serializer_data = {}
        if "delivery_order_file" in request.data:
            if request.data["delivery_order_file"] != "null":
                request.data.pop("delivery_order_file", None)
        if "bill_of_landing_file" in request.data:
            if request.data["bill_of_landing_file"] != "null":
                request.data.pop("bill_of_landing_file", None)
        shipment_data = request.data.copy()  # Work with a mutable copy
        for key, value in shipment_data.items():
            if value == "null":
                shipment_data[key] = None
        # Extract the nested container data
        # Correctly extract nested container data
        container_data = {
            key[len("container[") : -1]: value
            for key, value in shipment_data.items()
            if key.startswith("container[")
        }
        if container_data:
            serializer_data["container"] = container_data

        # fix this
        check_driver = shipment_data.get("driver")
        if check_driver:
            driver_id = int(check_driver)
            print(driver_id)

            if driver_id != shipment.driver_id:
                logging.warning("Current  Driver")
                logging.warning(driver_id)
                logging.warning("shipment  Driver")
                logging.warning(shipment.driver_id)
                serializer_data["status"] = "Assigned"

        date_format = "%Y/%m/%d"

        # Convert string to date
        assigned_date = shipment_data.get("assigned_date")

        if assigned_date:
            # if shipment.assigned_date is None:
            convert_assigned = datetime.strptime(assigned_date, date_format).date()
            shipment.assigned_date = convert_assigned
            serializer_data["assigned_date"] = convert_assigned
            shipment_data.pop("assigned_date")

        if shipment.assigned_date is None and assigned_date is None:
            try:
                shipment_data.pop("assigned_date")
            except KeyError:
                return Response(
                    {"error": "Assign Date Required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        shipment_status = shipment_data.get("status")
        if shipment_status == "Picked Up":
            if shipment.warehouse is None:
                return Response(
                    {"error": "Warehouse is not assigned to this shipment"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                serializer_data["pickedup_date"] = timezone.now()
                serializer_data["status"] = "Picked Up"
        if shipment_status == "Accepted":
            serializer_data["warehouse_accepted_date"] = timezone.now()
            shipment.warehouse_accepted_date = timezone.now()
            shipment.save()
            generate_shipment_pdf(shipment)
            shipment.save()

        if shipment_status == "Delivered":
            serializer_data["driver_delivered_date"] = timezone.now()

        if shipment_status == "Returned Empty":
            if shipment.status != "Accepted":
                return Response(
                    {"error": "Shipment is not accepted"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # shipment_data.pop("delivery_order_file", None)
        # shipment_data.pop("bill_of_landing_file", None)
        for key, value in shipment_data.items():
            if not key.startswith("container["):
                serializer_data[key] = value
        if "delivery_order_file" in request.FILES:
            serializer_data["delivery_order_file"] = request.FILES[
                "delivery_order_file"
            ]
        # else:
        #     serializer_data["delivery_order_file"] = None
        if "bill_of_landing_file" in request.FILES:
            serializer_data["bill_of_landing_file"] = request.FILES[
                "bill_of_landing_file"
            ]
        # else:
        #     serializer_data["bill_of_landing_file"] = None
        serializer = ShipmentUpdateSerializer(
            shipment, data=serializer_data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            logging.warning("Shipment SAVED")
            logging.warning(" Shipment Update Status")
            logging.warning(shipment.status)
            notification_message = f"Container {shipment.container.container_number} has been {shipment.status}."
            if current_user_type == "driver":
                if shipment.warehouse:
                    create_and_send_notification(
                        shipment.warehouse.user,
                        shipment.container.container_number,
                        notification_message,
                        shipment.status,
                        shipment.id,
                    )
                create_and_send_notification(
                    shipment.created_by,
                    shipment.container.container_number,
                    notification_message,
                    shipment.status,
                    shipment.id,
                )
            if current_user_type == "warehouse":
                if shipment.driver:
                    create_and_send_notification(
                        shipment.driver.user,
                        shipment.container.container_number,
                        notification_message,
                        shipment.status,
                        shipment.id,
                    )
                create_and_send_notification(
                    shipment.created_by,
                    shipment.container.container_number,
                    notification_message,
                    shipment.status,
                    shipment.id,
                )

            if current_user_type == "backoffice":
                if shipment.warehouse:
                    create_and_send_notification(
                        shipment.warehouse.user,
                        shipment.container.container_number,
                        notification_message,
                        shipment.status,
                        shipment.id,
                    )
                if shipment.driver:
                    create_and_send_notification(
                        shipment.driver.user,
                        shipment.container.container_number,
                        notification_message,
                        shipment.status,
                        shipment.id,
                    )

            if platform == "mobile":
                serializer = ShipmentSerializerMobileView(shipment)

                return Response(
                    {
                        "success": "Shipment Updated",
                        "data": serializer.data,
                    },
                    status=status.HTTP_202_ACCEPTED,
                )

            else:
                logging.warning("Notifications SENT")
                return Response(
                    {
                        "success": "Shipment Updated",
                    },
                    status=status.HTTP_202_ACCEPTED,
                )
        else:
            logging.warning(serializer.errors)
            return Response(
                {"error": "Shipment not Updated"}, status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request, pk, *args, **kwargs):

        shipment = self.get_object(pk)
        if not shipment:
            return Response(
                {"error": "Shipment Does not exist"}, status=status.HTTP_404_NOT_FOUND
            )
        shipment.is_deleted = True  # Perform the soft delete
        shipment.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BasicPagination(PageNumberPagination):
    page_size = 10


class CustomerShipmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get("search", None)
        # Fetch all WarehouseUsers and AssociateCompanies
        backoffice_user, _ = BackOfficeUser.objects.get_or_create(user=request.user)
        company_id = backoffice_user.company_id

        warehouses_query = WarehouseUser.objects.all()
        companies_query = AssociateCompany.objects.filter(company_id=company_id).all()
        if search:
            warehouses_query = warehouses_query.filter(
                company__company_name__icontains=search
            )
            companies_query = companies_query.filter(
                associate_company_name__icontains=search
            )

        # Fetch latest shipment for each WarehouseUser
        for warehouse in warehouses_query:
            latest_shipment = (
                Shipment.objects.filter(
                    warehouse=warehouse, status__in=["Picked Up", "Assigned"]
                )
                .order_by("-updated_at")
                .first()
            )
            warehouse.latest_shipment = latest_shipment

        # Fetch latest shipment for each AssociateCompany
        for company in companies_query:
            latest_shipment = (
                Shipment.objects.filter(
                    customer=company, status__in=["Picked Up", "Assigned"]
                )
                .order_by("-updated_at")
                .first()
            )
            company.latest_shipment = latest_shipment

        # Serialize data
        warehouse_data = CustomerWarehouseSerializer(
            warehouses_query, many=True, context={"request": request}
        ).data
        company_data = CustomerCompanySerializer(
            companies_query, many=True, context={"request": request}
        ).data

        combined_data = []

        # Add warehouse data with adjustments
        for warehouse in warehouse_data:
            # Adjust the warehouse data here as needed
            combined_data.append(
                {
                    "id": warehouse["id"],
                    "latest_shipment": warehouse.get("latest_shipment"),
                    "type": "Warehouse",
                    "responsible_person_name": warehouse.get("user")["first_name"]
                    + " "
                    + warehouse.get("user")["last_name"],
                    "company_name": warehouse.get("company")["company_name"],
                    "company_email": warehouse.get("company")["company_email"],
                    "company_phone_number": warehouse.get("company")[
                        "company_phone_number"
                    ],
                    "profile_picture": warehouse.get("user")["profile_picture"],
                    "created_at": warehouse.get("created_at"),
                    "updated_at": warehouse.get("updated_at"),
                }
            )

        # Add company data with adjustments
        for company in company_data:
            # Adjust the company data here as needed
            combined_data.append(
                {
                    "id": company["id"],
                    "latest_shipment": company.get("latest_shipment"),
                    "type": "Company",
                    "responsible_person_name": company.get("responsible_person_name"),
                    "company_name": company.get("associate_company_name"),
                    "company_email": company.get("associate_company_email"),
                    "company_phone_number": company.get("phone"),
                    "profile_picture": None,
                    "created_at": company.get("created_at"),
                    "updated_at": company.get("updated_at"),
                }
            )
            # Sort the combined data by 'updated_at' in descending order
        sorted_combined_data = sorted(
            combined_data, key=lambda x: parse(x["updated_at"]), reverse=True
        )

        # Implement manual pagination on the sorted_combined_data
        page = request.query_params.get("page", 1)
        paginator = Paginator(sorted_combined_data, 10)  # Adjust page size as needed
        try:
            paginated_data = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_data = paginator.page(1)
        except EmptyPage:
            # If page is out of range, deliver last page of results.
            paginated_data = paginator.page(paginator.num_pages)

        # Construct the paginated response manually
        return Response(
            {
                "count": paginator.count,
                "next": paginated_data.has_next(),
                "previous": paginated_data.has_previous(),
                "results": paginated_data.object_list,
            }
        )
        # return paginator.get_paginated_response(sorted_combined_data)


class CustomerShipmentsHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):

        shipment_type = request.query_params.get("type")
        status = request.query_params.get("status")
        container_number = request.query_params.get("container_number", None)
        shipments_query = Shipment.objects.all()

        # Default status filters if not provided
        if not status:
            status = ["Queued", "Picked Up", "Assigned"]
        else:
            status = ["Delivered", "Returned Empty"]

        # Filter shipments based on type and ID
        if shipment_type == "warehouse":
            shipments_query = shipments_query.filter(warehouse_id=id, status__in=status)
        elif shipment_type == "company":
            shipments_query = shipments_query.filter(customer_id=id, status__in=status)
        else:
            return Response(
                {"error": 'Invalid type parameter. Must be "warehouse" or "company".'},
                status=400,
            )
        if container_number:
            shipments_query = shipments_query.filter(
                container__container_number__icontains=container_number
            )

        # serializer = ShipmentSerializer(shipments, many=True)

        paginator = BasicPagination()
        paginated_shipments = paginator.paginate_queryset(shipments_query, request)
        serializer = ShipmentSerializer(
            paginated_shipments, many=True, context={"request": request}
        )

        return paginator.get_paginated_response(serializer.data)


class DashboardStatsAPIView(APIView):
    permission_classes = [IsBackofficeUser]

    def get(self, request, *args, **kwargs):
        backoffice_user, _ = BackOfficeUser.objects.get_or_create(user=request.user)
        company_id = backoffice_user.company_id

        today = timezone.now().date()
        today_shipment_count = Shipment.objects.filter(
            created_at__date=today, created_by=request.user, is_deleted=False
        ).count()
        total_shipment_count = Shipment.objects.filter(
            created_by=request.user, is_deleted=False
        ).count()

        total_driver_count = Driver.objects.all().count()
        associate_company_count = AssociateCompany.objects.filter(
            company_id=company_id
        ).count()

        shipment_history_count = Shipment.objects.filter(
            created_at__lte=today, created_by=request.user, is_deleted=False
        ).count()

        stats = {
            "today_shipment": today_shipment_count,
            "total_shipment": total_shipment_count,
            "total_driver": total_driver_count,
            "associate_company": associate_company_count,
            "shipment_history": shipment_history_count,
        }

        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)
