from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from .models import OLTInfraCharges

def bulk_add_infra_charges(charges_data_list):
    """
    Args:
        charges_data_list (list): A list of dictionaries containing your fields.
        Example: [{'OLT_id': 1, 'Financial_Year': '2025-26', 'applicableInfraCharges': 12000}, ...]
    """
    unsaved_instances = []
    
    # Wrap in a transaction so if one row fails validation, nothing gets written
    with transaction.atomic():
        for data in charges_data_list:
            # 1. Instantiate the model object in memory
            instance = OLTInfraCharges(**data)
            
            # 2. Run the logic manually since bulk_create skips save()
            try:
                # This runs your custom validation AND calculates Previous_dues
                instance.clean() 
            except ValidationError as e:
                # If any row breaks business logic, stop execution and alert the client
                raise DRFValidationError({
                    "error": f"Validation failed for OLT {instance.OLT_id} during bulk build.",
                    "details": e.message_dict
                })
            
            unsaved_instances.append(instance)
            
        # 3. Perform a single database hit to insert all validated rows
        # batch_size optimization prevents hitting database limits on massive loads
        created_objects = OLTInfraCharges.objects.bulk_create(unsaved_instances, batch_size=500)
        
    return created_objects
# -----------------------------------------------------------------------
# -----------------------------------------------------------------------
# -----------------------------------------------------------------------

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import OLTInfraCharges
from .serializers import OLTInfraChargesSerializer

class OLTInfraChargesViewSet(viewsets.ModelViewSet):
    queryset = OLTInfraCharges.objects.all()
    serializer_serializer = OLTInfraChargesSerializer

    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create_charges(self, request):
        # Expecting a list of JSON objects from the client
        if not isinstance(request.data, list):
            return Response(
                {"error": "Expected a list of objects under bulk creation payload."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Optional: You can pass the raw dictionaries to your bulk script safely
        try:
            created_records = bulk_add_infra_charges(request.data)
            return Response(
                {"status": f"Successfully bulk created {len(created_records)} records."},
                status=status.HTTP_201_CREATED
            )
        except DRFValidationError as api_err:
            return Response(api_err.detail, status=status.HTTP_400_BAD_REQUEST)

