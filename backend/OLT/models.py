from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class OLT(models.Model):
    LOCATION_CHOICES = [
        ('BSNL premises', 'BSNL premises'),
        ('Own premises', 'Own premises'),
    ]
    added_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='OLTs')
    created_at = models.DateTimeField(auto_now_add=True)
    OLT_IP = models.GenericIPAddressField(unique=True)
    OA_Name = models.CharField(max_length=3)
    dateOfInstallation = models.DateField()
    franchisee_Name = models.CharField(max_length=50)
    located_at = models.CharField(max_length=20, choices=LOCATION_CHOICES)
    REM_ID = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.OLT_IP} - {self.OA_Name}"


class OLTInfraCharges(models.Model):
    OLT = models.ForeignKey('OLT', on_delete=models.PROTECT, related_name="infra_charges")
    financial_Year = models.CharField(max_length=9, help_text="Enter year like 2025-26")
    previous_dues = models.IntegerField(default=0)
    applicableInfraCharges = models.IntegerField(default=0)
    applicableSecurityDeposit = models.IntegerField(default=0)
    applicableOneTimeCharges = models.IntegerField(default=0)
    infraChargesWaiver = models.IntegerField(default=0)
    securityDepositWaiver = models.IntegerField(default=0)
    oneTimeChargesWaiver = models.IntegerField(default=0)
    
    REM_Invoice_No = models.CharField(max_length=30, blank=True, null=True)
    amount_Collected = models.IntegerField(default=0)

    class Meta:
        # Fixed field name casing from 'Financial_Year' to 'financial_Year'
        unique_together = ('OLT', 'financial_Year')

    @property
    def TotalApplicableChargesThisYear(self):
        # Fixed casing variations across waiver attributes
        infra_net = (self.applicableInfraCharges - self.infraChargesWaiver) * 1.18
        security_net = (self.applicableSecurityDeposit - self.securityDepositWaiver)
        onetime_net = (self.applicableOneTimeCharges - self.oneTimeChargesWaiver) * 1.18
        return int(infra_net + security_net + onetime_net)

    @property
    def Amount_Balance(self):
        # Fixed the lowercase casing mismatch to match the property method name exactly
        return self.previous_dues + self.TotalApplicableChargesThisYear - self.amount_Collected

    def clean(self):
        super().clean()     
        # 1. Location Validation
        if self.OLT and self.OLT.located_at != 'BSNL premises':
            raise ValidationError({
                'OLT': "Infra charges are applicable only for OLTs located in 'BSNL premises'."
            })
        
        # 2. Set base previous dues upon original instantiation ONLY
        if self.pk is None and self.financial_Year and self.OLT_id:
            try:
                parts = self.financial_Year.split('-')
                if len(parts) == 2:
                    current_start_year = int(parts[0])
                    prev_start_year = current_start_year - 1
                    prev_end_year = current_start_year
                    
                    prev_end_suffix = str(prev_end_year)[2:]
                    prev_fy_string = f"{prev_start_year}-{prev_end_suffix}"

                    # Removed 'OA' filter keyword since it doesn't exist on this model table directly
                    prev_record = OLTInfraCharges.objects.filter(
                        OLT=self.OLT,
                        financial_Year=prev_fy_string
                    ).first()

                    if prev_record:
                        # Fixed variable casing from Previous_dues to previous_dues
                        self.previous_dues = int(prev_record.Amount_Balance)        
            except (ValueError, IndexError):
                pass

    def save(self, *args, **kwargs):
        # 1. Run basic field checks and clean validation rules
        self.full_clean()
        
        # 2. Calculate balance shifts if this record is modifying numbers
        is_new = self.pk is None
        old_balance = 0
        if not is_new:
            old_instance = OLTInfraCharges.objects.get(pk=self.pk)
            old_balance = old_instance.Amount_Balance
            
        # 3. Save the current record row values safely to the database
        super().save(*args, **kwargs)
        
        # 4. Net Adjustment Forward Chain: Apply delta variations to the next timeline entry
        next_year_record = self.get_next_year_record()
        if next_year_record:
            if is_new:
                # Rule: If new record added, add its total balance to next year's starting dues
                next_year_record.previous_dues += self.Amount_Balance
            else:
                # Rule: If modifying data, compute the shift difference and push the adjustment delta
                balance_delta = self.Amount_Balance - old_balance
                next_year_record.previous_dues += balance_delta
                
            # Re-saving cascades the change further up the timeline if more future rows exist
            next_year_record.save()

    def delete(self, *args, **kwargs):
        next_year_record = self.get_next_year_record()
        
        if next_year_record:
            # Rule: If row gets dropped, deduct its closing balance impact from next year's opening dues
            next_year_record.previous_dues -= self.Amount_Balance
            next_year_record.save()
            
        # Physically erase row from database
        super().delete(*args, **kwargs)

    def get_next_year_record(self):
        """Calculates string components to scan for the immediate subsequent financial year row"""
        try:
            parts = self.financial_Year.split('-')
            if len(parts) == 2:
                current_start = int(parts[0])
                next_start = current_start + 1
                next_end_suffix = str(next_start + 1)[2:]
                next_fy_string = f"{next_start}-{next_end_suffix}"
                
                return OLTInfraCharges.objects.filter(
                    OLT=self.OLT,
                    financial_Year=next_fy_string
                ).first()
        except (ValueError, IndexError):
            return None
