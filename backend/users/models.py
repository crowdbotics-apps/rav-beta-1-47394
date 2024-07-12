from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


# from backoffice.models import Company
class User(AbstractUser):
    # WARNING!
    """
    Some officially supported features of Crowdbotics Dashboard depend on the initial
    state of this User model (Such as the creation of superusers using the CLI
    or password reset in the dashboard). Changing, extending, or modifying this model
    may lead to unexpected bugs and or behaviors in the automated flows provided
    by Crowdbotics. Change it at your own risk.


    This model represents the User instance of the system, login system and
    everything that relates with an `User` is represented by this model.
    """

    # First Name and Last Name do not cover name patterns
    # around the globe.
    USER_TYPE_CHOICES = [
        ("backoffice", "Backoffice"),
        ("warehouse", "Warehouse"),
        ("driver", "Driver"),
    ]
    name = models.CharField(_("Name of User"), blank=True, null=True, max_length=255)
    phone_number = models.CharField(max_length=15, blank=True)
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", null=True, blank=True
    )
    is_onboarded = models.BooleanField(default=False)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = []
    def get_absolute_url(self):
        """
        get_absolute_url
        """
        return reverse("users:detail", kwargs={"username": self.username})

    def __str__(self):
        return self.email


class Driver(models.Model):
    """
    Driver
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver")
    # setting company name to char but it shouldbe foreign company key MVP-2
    company_name = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    emergency_number = models.CharField(max_length=100, blank=True, null=True)
    # Add driver-specific fields here
    license_number = models.CharField(max_length=20, blank=True, null=True)
    registration_state = models.CharField(max_length=50, blank=True, null=True)
    # cdl_number = models.CharField(max_length=20)  # Commercial Driver's License Number
    twic_number = models.CharField(
        max_length=20, blank=True, null=True
    )  # Transportation Worker Identification Credential
    dot_number = models.CharField(
        max_length=20, blank=True, null=True
    )  # Department of Transportation Number
    dg_certification = models.CharField(
        max_length=20, blank=True, null=True
    )  # Dangerous Goods Certification
    driver_payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email


class BackOfficeUser(models.Model):
    """
    BackOfficeUser
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="backoffice"
    )
    # Add backoffice-specific fields here

    company = models.ForeignKey(
        "backoffice.Company",
        on_delete=models.CASCADE,
        related_name="backoffice_users",
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email


class WarehouseUser(models.Model):
    """
    WarehouseUser
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="warehouse"
    )
    company = models.ForeignKey(
        "backoffice.Company",
        on_delete=models.CASCADE,
        related_name="warehouse_users",
        null=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add warehouse-specific fields here

    def __str__(self):
        return self.user.email


class Feedback(models.Model):
    """
    FEEDBACK
    """

    subject = models.CharField(max_length=100)
    message = models.TextField()
    email = models.EmailField()

    def __str__(self):
        return self.subject


class Notification(models.Model):
    """
    This class represents a Notification in a Python application.
    """

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
    )
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=255, null=True)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    shipment = models.ForeignKey(
        "backoffice.Shipment",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,  # Assuming a notification might not always be related to a shipment
    )
    # New JSONField for storing additional data
    data = models.JSONField(null=True, blank=True)


class Device(models.Model):
    """
    This class represents a device in a Python application.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="devices",
        null=True,
    )
    registration_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
