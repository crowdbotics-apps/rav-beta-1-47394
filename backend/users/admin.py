from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from users.forms import UserChangeForm, UserCreationForm

from .models import (
    BackOfficeUser,
    Device,
    Driver,
    Feedback,
    Notification,
    User,
    WarehouseUser,
)

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (("User", {"fields": ("name",)}),) + auth_admin.UserAdmin.fieldsets
    list_display = ["email", "name", "is_superuser", "phone_number", "user_type"]
    search_fields = ["email"]


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "license_number")
    search_fields = ("user__email", "company_name")

    def user_email(self, obj):
        return obj.user.email

    user_email.admin_order_field = "user__email"  # Allows column order sorting
    user_email.short_description = "User Email"  # Column header


@admin.register(BackOfficeUser)
class BackOfficeUserAdmin(admin.ModelAdmin):

    list_display = ("user", "company_name")
    search_fields = ("user__email", "company__company_email", "company__company_name")

    def company_name(self, obj):
        return obj.company.company_name if obj.company else None

    company_name.admin_order_field = (
        "company__company_name"  # Allows column order sorting
    )
    company_name.short_description = "Company Name"  # Column header

    # Since 'user' is a OneToOneField, you can access it directly in list_display,
    # but if you need to show the email in the list, you can define a method like this:
    def user_email(self, obj):
        return obj.user.email

    user_email.admin_order_field = "user__email"  # Allows column order sorting
    user_email.short_description = "User Email"  # Column header


@admin.register(WarehouseUser)
class WarehouseUserAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "company_name",
    )
    search_fields = ("user__email", "company__company_email", "company__company_name")

    def company_name(self, obj):
        return obj.company.company_name if obj.company else None

    company_name.admin_order_field = (
        "company__company_name"  # Allows column order sorting
    )
    company_name.short_description = "Company Name"  # Column header

    # Since 'user' is a OneToOneField, you can access it directly in list_display,
    # but if you need to show the email in the list, you can define a method like this:
    def user_email(self, obj):
        return obj.user.email

    user_email.admin_order_field = "user__email"  # Allows column order sorting
    user_email.short_description = "User Email"  # Column header


admin.site.register(Feedback)
# admin.site.register(Notification)


@admin.register(Device)
class Device(admin.ModelAdmin):
    list_display = ["user", "registration_id"]
    search_fields = ["registration_id", "user"]
