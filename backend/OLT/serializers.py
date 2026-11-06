from rest_framework import serializers
from django.contrib.auth.models import User
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
        read_only_fields = ['created_at']

class OLTInfraChargesSerializer(serializers.ModelSerializer):
    TotalApplicableChargesThisYear = serializers.ReadOnlyField()
    Amount_Balance = serializers.ReadOnlyField()
    
    # Exposes hardware info dynamically without executing extra standalone requests
    olt_detail = OLTSerializer(source='OLT', read_only=True)

    class Meta:
        model = OLTInfraCharges
        fields = [
            'id', 'OLT', 'olt_detail', 'Financial_Year', 'Previous_dues',
            'applicableInfraCharges', 'applicableSecurityDeposit', 'applicableOneTimeCharges',
            'infraChargesWaiver', 'securityDepositWaiver', 'oneTimeChargesWaiver',
            'REM_Invoice_No', 'amount_Collected', 
            'TotalApplicableChargesThisYear', 'Amount_Balance'
        ]
        # Keep Previous_dues read_only if you want the system calculation to strictly govern it
        read_only_fields = ['previous_dues']

    def validate(self, attrs):
        # Form an unsaved model instance out of the validated data payloads
        instance = OLTInfraCharges(**attrs)
        
        # Trigger the model clean engine explicitly 
        try:
            instance.clean()
        except serializers.ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
            
        return attrs