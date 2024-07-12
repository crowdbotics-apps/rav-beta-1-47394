from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import BackOfficeUser, Driver, WarehouseUser

from .models import AssociateCompany, Company
from .permissions import IsBackofficeUser
from .serializers import AssociateCompanySerializer, CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsBackofficeUser]


class AssociateCompanyViewSet(viewsets.ModelViewSet):
    queryset = AssociateCompany.objects.all()
    serializer_class = AssociateCompanySerializer
    permission_classes = [IsBackofficeUser]
    pagination_class = None

    def create(self, request, *args, **kwargs):
        user_id = request.data.get("user_id")

        # Ensure user_id is provided and valid
        if not user_id:
            return Response(
                {"error": "user_id must be provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Find the associated Company through the BackOfficeUser
        backoffice_user = get_object_or_404(BackOfficeUser, user_id=user_id)
        if not backoffice_user.company:
            return Response(
                {"error": "No company associated with this backoffice user"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update the request data with the company ID
        request.data.update({"company": backoffice_user.company.id})

        # Continue with the standard create process
        return super(AssociateCompanyViewSet, self).create(request, *args, **kwargs)
