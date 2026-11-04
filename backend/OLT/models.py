from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class OLT(models.Model):
    LOCATION_CHOICES = [
        ('BSNL premises', 'BSNL premises'),
        ('Own premises', 'Own premises'),
    ]

    added_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='OLTs') # Changed to PROTECT as a safeguard
    OLT_IP = models.GenericIPAddressField(unique=True)
    OA_Name = models.CharField(max_length=3)
    created_at = models.DateTimeField(auto_now_add=True)
    DateOfInstallation = models.DateField()
    Franchisee_Name = models.CharField(max_length=50)
    Located_at = models.CharField(max_length=20, choices=LOCATION_CHOICES)

    def __str__(self):
        return self.OLT_IP
    
    def delete(self, *args, **kwargs):
        """Overrides the delete method to prevent deletion of OLT records entirely."""
        raise ValidationError("OLT records cannot be deleted once added.")

    def hard_delete(self, *args, **kwargs):
        """Use this internal method only if you ever need to bypass the restriction programmatically."""
        super().delete(*args, **kwargs)
    


class OLTInfraCharges(models.Model):
    OLT = models.ForeignKey('OLT', on_delete=models.PROTECT, related_name="infra_charges")
    REM_ID = models.CharField(max_length=30)
    # Financial Year (e.g., "2025-26")
    Financial_Year = models.CharField(max_length=9, help_text="Enter year like 2025-26")
    
    Previous_dues = models.IntegerField(default=0)
    applicableInfraCharges = models.IntegerField(default=0)
    applicableSecurityDeposit = models.IntegerField(default=0)
    applicableOneTimeCharges = models.IntegerField(default=0)
    InfraChargesWaiver = models.IntegerField(default=0)
    SecurityDepositWaiver = models.IntegerField(default=0)
    OneTimeChargesWaiver = models.IntegerField(default=0)
    
    REM_Invoice_Generated = models.CharField(max_length=30, blank=True, null=True)
    Amount_Collected = models.IntegerField(default=0)

    class Meta:
        # Ensures a specific OLT can only have one entry per Financial Year
        unique_together = ('OLT', 'Financial_Year')

    @property
    def TotalApplicableChargesThisYear(self):
        infra_net = (self.applicableInfraCharges - self.InfraChargesWaiver) * 1.18
        security_net = (self.applicableSecurityDeposit - self.SecurityDepositWaiver)
        onetime_net = (self.applicableOneTimeCharges - self.OneTimeChargesWaiver) * 1.18
        return infra_net + security_net + onetime_net

    @property
    def Amount_Balance(self):
        return self.Previous_dues + self.TotalApplicableChargesThisYear - self.Amount_Collected

    def clean(self):
        super().clean()
        
        # 1. Check if OLT is located in BSNL premises
        if self.OLT and self.OLT.Located_at != 'BSNL premises':
            raise ValidationError({
                'OLT': "Infra charges can only be entered for OLTs located in 'BSNL premises'."
            })

        # 2. Automatically compute and carry forward Previous_dues from the last financial year
        if self.Financial_Year and self.OLT_id:
            try:
                # Parse financial year string (expects format like "2025-26")
                parts = self.Financial_Year.split('-')
                if len(parts) == 2:
                    current_start_year = int(parts[0])
                    prev_start_year = current_start_year - 1
                    prev_end_year_suffix = parts[1] # e.g. "26" becomes "25" logically or handled via arithmetic
                    
                    # Compute previous financial year string (e.g., "2025-26" -> "2024-25")
                    prev_start_str = str(prev_start_year)
                    prev_end_str = str(int(parts[1]) - 1).zfill(2)
                    prev_fy_string = f"{prev_start_str}-{prev_end_str}"

                    # Look up the previous year's record for this specific OLT
                    prev_record = OLTInfraCharges.objects.filter(
                        OLT=self.OLT, 
                        Financial_Year=prev_fy_string
                    ).exclude(pk=self.pk).first() # exclude self in case of updates

                    if prev_record:
                        # Carry forward the closing balance (Amount_Balance) of last year as previous dues
                        self.Previous_dues = int(prev_record.Amount_Balance)
            except (ValueError, IndexError):
                # If the string format isn't strictly standard, bypass auto-calculation safely
                pass

    def save(self, *args, **kwargs):
        # Trigger full_clean() so validation and auto-calculation run when saving
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.OLT.OLT_IP} - {self.Financial_Year}"