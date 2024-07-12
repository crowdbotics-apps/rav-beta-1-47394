from core.enums import ShipmentStatus
from django.conf import settings
from django.db import models
from users.models import Driver, WarehouseUser  # Import User model from users app


class Company(models.Model):
    company_name = models.CharField(max_length=255)
    company_email = models.EmailField()
    company_phone_number = models.CharField(max_length=20)
    address = models.TextField()
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    company_bio = models.TextField()
    company_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name


class AssociateCompany(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="associate_companies"
    )
    responsible_person_name = models.CharField(max_length=255)
    associate_company_name = models.CharField(max_length=255, blank=True, null=True)
    associate_company_email = models.EmailField(blank=True, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    associate_company_bio = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.responsible_person_name} - {self.associate_company_name}"

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"


class Container(models.Model):
    container_number = models.CharField(max_length=255)

    size = models.CharField(
        max_length=50, null=True, blank=True
    )  # Assuming size is an integer value
    type = models.CharField(max_length=50, null=True, blank=True)
    owner = models.CharField(
        max_length=255, null=True, blank=True
    )  # Owner's name or identifier
    chassis_number = models.CharField(max_length=255, null=True, blank=True)
    chassis_size = models.CharField(max_length=255, null=True, blank=True)
    chassis_type = models.CharField(max_length=255, null=True, blank=True)

    genset_number = models.CharField(max_length=255, null=True, blank=True)
    temperature = models.CharField(max_length=255, null=True, blank=True)

    scac = models.CharField(
        max_length=255, null=True, blank=True
    )  # Standard Carrier Alpha Code

    hazmat = models.BooleanField(default=False)
    overweight = models.BooleanField(default=False)
    overheight = models.BooleanField(default=False)
    hot = models.BooleanField(default=False)
    genset = models.BooleanField(default=False)
    liquor = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.container_number


class Shipment(models.Model):
    container = models.ForeignKey(
        Container, on_delete=models.CASCADE, related_name="container"
    )
    customer = models.ForeignKey(
        AssociateCompany,
        on_delete=models.SET_NULL,
        null=True,
        related_name="customer",
        blank=True,
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        swappable=True,
        null=True,
        related_name="driver",
        blank=True,
    )
    warehouse = models.ForeignKey(
        WarehouseUser,
        on_delete=models.SET_NULL,
        swappable=True,
        null=True,
        blank=True,
        related_name="warehouse",
    )

    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.value) for status in ShipmentStatus],
    )

    assigned_date = models.DateField(null=True, blank=True)
    warehouse_accepted_date = models.DateTimeField(null=True, blank=True)
    driver_delivered_date = models.DateTimeField(null=True, blank=True)
    # LOAD INFO
    pickup_location = models.CharField(max_length=255, null=True, blank=True)
    delivery_location = models.CharField(max_length=255, null=True, blank=True)
    chassis_location = models.CharField(max_length=255, null=True, blank=True)
    return_location = models.CharField(max_length=255, null=True, blank=True)

    return_time = models.CharField(max_length=255, null=True, blank=True)
    pickup_time = models.CharField(max_length=255, null=True, blank=True)
    # delivery_time = models.DateTimeField(null=True, blank=True)

    # Add fields from the Dates section
    vessel_eta = models.CharField(max_length=255, null=True, blank=True)
    last_free_day = models.CharField(max_length=255, null=True, blank=True)
    discharged_date = models.CharField(max_length=255, null=True, blank=True)
    outgate_date = models.CharField(max_length=255, null=True, blank=True)
    ingate_date = models.CharField(max_length=255, null=True, blank=True)
    empty_date = models.CharField(max_length=255, null=True, blank=True)
    return_day = models.CharField(max_length=255, null=True, blank=True)
    pickedup_date = models.DateTimeField(null=True, blank=True)
    # Referenced fields
    master_bill_of_landing = models.CharField(max_length=255, null=True, blank=True)
    house_bill_of_landing = models.CharField(max_length=255, null=True, blank=True)
    seal_number = models.CharField(max_length=255, null=True, blank=True)
    reference_number = models.CharField(max_length=255, null=True, blank=True)
    vessel_name = models.CharField(max_length=255, null=True, blank=True)
    voyage = models.CharField(max_length=255, null=True, blank=True)
    shipment_number = models.CharField(max_length=255, null=True, blank=True)
    pickup_number = models.CharField(max_length=255, null=True, blank=True)
    appointment_number = models.CharField(max_length=255, null=True, blank=True)
    return_number = models.CharField(max_length=255, null=True, blank=True)
    reservation_number = models.CharField(max_length=255, null=True, blank=True)
    # DELIVERY INFO

    delivery_date = models.CharField(max_length=255, null=True, blank=True)
    delivery_from = models.CharField(max_length=255, null=True, blank=True)
    delivery_to = models.CharField(max_length=255, null=True, blank=True)

    delivery_order = models.BooleanField(default=False)
    delivery_order_file = models.FileField(
        upload_to="delivery_orders/", null=True, blank=True
    )
    bill_of_landing = models.BooleanField(default=False)
    bill_of_landing_file = models.FileField(
        upload_to="bills_of_landing/", null=True, blank=True
    )
    proof_of_delivery_file = models.FileField(
        upload_to="proof_of_delivery/", null=True, blank=True
    )

    # For the Container Availability section
    freight_hold = models.BooleanField(default=False)
    customs_hold = models.BooleanField(default=False)
    carrier_hold = models.BooleanField(default=False)

    # Add fields from the Freight Info section
    commodity = models.CharField(max_length=255, null=True, blank=True)
    piece_count = models.IntegerField(null=True, blank=True)
    weight_lbs = models.IntegerField(null=True, blank=True)
    weight_kgs = models.IntegerField(null=True, blank=True)
    pallet_count = models.IntegerField(null=True, blank=True)
    freight_description = models.TextField(null=True, blank=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_by",
        null=True,
    )

    def __str__(self):
        return f"Shipment - {self.container.container_number}"
