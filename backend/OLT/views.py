from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import ProtectedError
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated

from .models import OLT, OLTInfraCharges
from .serializers import OLTSerializer, OLTInfraChargesSerializer


def to_drf_error(e):
    """Django ValidationError -> DRF ValidationError (handles dict and plain-message forms)."""
    if hasattr(e, 'error_dict'):
        return DRFValidationError(e.message_dict)
    return DRFValidationError(e.messages)


class OLTViewSet(viewsets.ModelViewSet):
    queryset = OLT.objects.select_related('added_by')
    serializer_class = OLTSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            serializer.save(added_by=self.request.user)
        except DjangoValidationError as e:
            raise to_drf_error(e)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise to_drf_error(e)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise DRFValidationError(
                "Cannot delete an OLT that has infra charge records."
            )


class OLTInfraChargesViewSet(viewsets.ModelViewSet):
    queryset = OLTInfraCharges.objects.select_related('OLT__added_by')
    serializer_class = OLTInfraChargesSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise to_drf_error(e)

    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise to_drf_error(e)

    def perform_destroy(self, instance):
        if instance.amount_Balance > 0:
            raise DRFValidationError(
                "Cannot delete a record that still has an active balance."
            )
        instance.delete()
