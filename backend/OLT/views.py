from django.shortcuts import render
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from .models import OLT, OLTInfraCharges
from .serializers import OLTSerializer, OLTInfraChargesSerializer
from rest_framework import viewsets

# Create your views here.

class OLTViewSet(viewsets.ModelViewSet):
    queryset = OLT.objects.all()
    serializer_class = OLTSerializer

    # Fixed parameter name to 'serializer' to avoid Django TypeErrors
    def perform_create(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict)
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict)
        
    def perform_destroy(self, instance):
        # Kept clean and simple since standard OLT hardware doesn't track active financial balances
        super().perform_destroy(instance)


###########################################################
class OLTInfraChargesViewSet(viewsets.ModelViewSet):
    queryset = OLTInfraCharges.objects.all()
    serializer_class = OLTInfraChargesSerializer

    # Fixed parameter name to 'serializer' here as well
    def perform_create(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict)
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict)
        
    def perform_destroy(self, instance):
        # Safely checks the active balance constraint on the billing records before allowing erasure
        if hasattr(instance, 'Amount_Balance') and instance.Amount_Balance > 0:
            raise DRFValidationError("Cannot delete a record that still has an active balance!")
        super().perform_destroy(instance)

