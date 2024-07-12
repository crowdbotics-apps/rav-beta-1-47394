from django.contrib import admin

from .models import AssociateCompany, Company, Container, Shipment

# Register your models here.


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = [
        "company_name",
        "company_email",
        "company_phone_number",
        "country",
        "city",
    ]
    search_fields = ["company_name", "company_email"]


@admin.register(AssociateCompany)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["responsible_person_name", "email", "phone", "company"]
    search_fields = ["responsible_person_name", "email", "company__company_name"]


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ["container_number", "owner", "size", "type"]
    search_fields = ["container_number", "owner"]


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        "get_container_number",
        "get_driver",
        "get_warehouse",
        "status",
    )
    list_filter = (
        "status",
        "driver",
        "warehouse",
    )  # Optional: To add filters by status or related objects
    search_fields = (
        "container__container_number",
        "driver__user__email",
        "warehouse__user__email",
    )

    def get_container_number(self, obj):
        return obj.container.container_number if obj.container else None

    get_container_number.admin_order_field = (
        "container__container_number"  # Allows column order sorting
    )
    get_container_number.short_description = "Container Number"  # Column header

    def get_driver(self, obj):
        return obj.driver.user.email if obj.driver else None

    get_driver.admin_order_field = "driver__user__email"  # Allows column order sorting
    get_driver.short_description = "Driver Email"  # Column header

    def get_warehouse(self, obj):
        return obj.warehouse.user.email if obj.warehouse else None

    get_warehouse.admin_order_field = (
        "warehouse__user__email"  # Allows column order sorting
    )
    get_warehouse.short_description = "Warehouse Email"  # Column header
