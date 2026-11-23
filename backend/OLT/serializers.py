import copy
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
# from django.contrib.auth.models import User
from .models import OLT, OLTInfraCharges
from api.serializers import UserSerializer

class OLTSerializer(serializers.ModelSerializer):
    # Read-only field to show profile details of the user who added it
    added_by_detail = UserSerializer(source='added_by', read_only=True)

    class Meta:
        model = OLT
        fields = [
            'id', 'added_by', 'added_by_detail', 'created_at', 
            'OLT_IP', 'OA_Name', 'dateOfInstallation', 
            'franchisee_Name', 'located_at', 'REM_ID'
        ]
        read_only_fields = ['created_at', 'added_by']

class OLTInfraChargesSerializer(serializers.ModelSerializer):
    # olt_detail = OLTSerializer()
    # TotalApplicableChargesThisYear = serializers.ReadOnlyField()
    # Amount_Balance = serializers.ReadOnlyField()
    
    # Exposes hardware info dynamically without executing extra standalone requests
    olt_detail = OLTSerializer(source='OLT', read_only=True)

    class Meta:
        model = OLTInfraCharges
        fields = [
            'id', 'OLT', 'olt_detail', 'financial_Year', 'previous_dues',
            'applicableInfraCharges', 'applicableSecurityDeposit', 'applicableOneTimeCharges',
            'infraChargesWaiver', 'securityDepositWaiver', 'oneTimeChargesWaiver',
            'REM_Invoice_No', 'amount_Collected', 
            'total_Applicable_Charges_This_Year', 'amount_Balance'
        ]
        # Keep Previous_dues read_only if you want the system calculation to strictly govern it
        read_only_fields = ['previous_dues',
                            'total_Applicable_Charges_This_Year',
                            'amount_Balance'
        ]

    def validate(self, attrs):
            if self.instance:
                # OLT and FY are locked after creation (model.save enforces this too)
                for f in ('OLT', 'financial_Year'):
                    if f in attrs and attrs[f] != getattr(self.instance, f):
                        raise serializers.ValidationError(
                            {f: "Cannot be changed after the record is created."}
                        )
                instance = copy.copy(self.instance)
                for k, v in attrs.items():
                    setattr(instance, k, v)
            else:
                instance = OLTInfraCharges(**attrs)

            try:
                instance.clean()
            except DjangoValidationError as e:
                raise serializers.ValidationError(
                    e.message_dict if hasattr(e, 'error_dict') else e.messages
                )
            return attrs