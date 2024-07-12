from rest_framework import permissions


class IsBackofficeUser(permissions.BasePermission):
    """
    Custom permission to only allow backoffice users to create an Associate Company.
    """

    def has_permission(self, request, view):
        # Check if the request method is POST and if the user is authenticated and a backoffice user
        if (
            request.method == "POST"
            or request.method == "PUT"
            or request.method == "PATCH"
            or request.method == "DELETE"
        ):
            return (
                request.user.is_authenticated and request.user.user_type == "backoffice"
            )
        if request.method == "GET":
            return request.user.is_authenticated


class IsDriverUser(permissions.BasePermission):
    """
    Custom permission to only allow backoffice users to create an Associate Company.
    """

    def has_permission(self, request, view):
        # Check if the request method is POST and if the user is authenticated and a backoffice user
        if (
            request.method == "POST"
            or request.method == "PUT"
            or request.method == "PATCH"
            or request.method == "DELETE"
        ):
            return request.user.is_authenticated and request.user.user_type == "driver"
        if request.method == "GET":
            return request.user.is_authenticated


class IsWarehouseUser(permissions.BasePermission):
    """
    Custom permission to only allow backoffice users to create an Associate Company.
    """

    def has_permission(self, request, view):
        # Check if the request method is POST and if the user is authenticated and a backoffice user
        if (
            request.method == "POST"
            or request.method == "PUT"
            or request.method == "PATCH"
            or request.method == "DELETE"
        ):
            return (
                request.user.is_authenticated and request.user.user_type == "warehouse"
            )
        if request.method == "GET":
            return request.user.is_authenticated
