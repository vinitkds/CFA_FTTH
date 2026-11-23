
import re

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class OLT(models.Model):

    LOCATION_CHOICES = [
        ('BSNL premises', 'BSNL premises'),
        ('Own premises', 'Own premises'),
    ]

    added_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='OLTs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    OLT_IP = models.GenericIPAddressField(unique=True)
    OA_Name = models.CharField(max_length=3)
    dateOfInstallation = models.DateField()
    franchisee_Name = models.CharField(max_length=50)
    located_at = models.CharField(
        max_length=20,
        choices=LOCATION_CHOICES
    )
    REM_ID = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.OLT_IP} - {self.OA_Name}"


class OLTInfraCharges(models.Model):

    OLT = models.ForeignKey(
        'OLT',
        on_delete=models.PROTECT,
        related_name="infra_charges"
    )

    financial_Year = models.CharField(
        max_length=7,
        help_text="Enter year like 2025-26"
    )

    previous_dues = models.IntegerField(default=0, editable=False)
    
    applicableInfraCharges = models.IntegerField(default=0)
    applicableSecurityDeposit = models.IntegerField(default=0)
    applicableOneTimeCharges = models.IntegerField(default=0)

    infraChargesWaiver = models.IntegerField(default=0)
    securityDepositWaiver = models.IntegerField(default=0)
    oneTimeChargesWaiver = models.IntegerField(default=0)

    REM_Invoice_No = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    total_Applicable_Charges_This_Year = models.IntegerField(default=0)
    amount_Collected = models.IntegerField(default=0)
    amount_Balance = models.IntegerField(default=0)

    class Meta:
        unique_together = ('OLT', 'financial_Year')
        ordering = ['financial_Year']

    def __str__(self):
        return f"{self.OLT} - {self.financial_Year}"

    # --------------------------------------------------
    # 1. FINANCIAL YEAR VALIDATION - 
    #       a. It valdates vald string in financial_year entered by user
    #       b. returns 203 from string in case financial year is 2023-24
    # --------------------------------------------------

    @staticmethod
    def get_year_start(financial_year):

        match = re.fullmatch(r'(\d{4})-(\d{2})', financial_year or '')

        if not match:
            raise ValueError("Invalid Financial Year format")

        start_year = int(match.group(1))
        end_suffix = int(match.group(2))

        if end_suffix != (start_year + 1) % 100:
            raise ValueError("Invalid Financial Year")

        return start_year

    # --------------------------------------------------
    # 2. TOTAL CHARGES CALCULATION
    # --------------------------------------------------

    def CalculateApplicableChargesThisYear(self):

        infra_net = (
            self.applicableInfraCharges - self.infraChargesWaiver
        ) * 1.18

        security_net = (
            self.applicableSecurityDeposit - self.securityDepositWaiver
        )

        onetime_net = (
            self.applicableOneTimeCharges - self.oneTimeChargesWaiver
        ) * 1.18

        return int(infra_net + security_net + onetime_net)

    # --------------------------------------------------
    # 3. CLOSING BALANCE
    # --------------------------------------------------

    def Calculate_Amount_Balance(self):

        return (
            self.previous_dues
            + self.total_Applicable_Charges_This_Year
            - self.amount_Collected
        )

    # --------------------------------------------------
    # 4. FIND PREVIOUS FINANCIAL YEAR RECORD - 
    # $$$$$$$$here recnt previous record is collected$$$$$$$$
    # first for selected line to be modified or deleted start_year string is identified
    # then all records for self.olt_Id extracted from table OLT Infra Charges
    # then using pk = self.pk selected record excluded
    # for year < selecte record previous records are uploaded as start_year_string, record to new object
    # then using max function and lambda function only recent FY record is extracted 
    # --------------------------------------------------

    def get_previous_year_record(self, lock=False):

        if not self.OLT_id:             
            return None

        current_year = self.get_year_start(self.financial_Year) # returns 2023 in case fy = 2023-24
        # selectedYearStartString = self.get_year_start(self.financial_Year) # returns 2023

        # get all OLTInfraCharges rows/records for given OLT
        records = OLTInfraCharges.objects.filter(
            OLT_id=self.OLT_id
        )

        if self.pk:     # check if selected row/record has a primary key
            records = records.exclude(pk=self.pk) # filters out the current record from the database query results and saves in records  

        if lock:
            records = records.select_for_update()

        previous_records = []

        for record in records:
            try:
                year = self.get_year_start(record.financial_Year)

                if year < current_year:
                    previous_records.append((year, record))

            except ValueError:
                continue

        if not previous_records:
            return None

        return max(previous_records, key=lambda x: x[0])[1]
    

    # --------------------------------------------------
    # 5. FIND NEXT FINANCIAL YEAR RECORD
    # $$$$$$$$here immediate next record available is collected$$$$$$$$
    # first for selected line to be modified or deleted start_year string is identified
    # then all records for self.olt_Id extracted from table OLT Infra Charges
    # then using pk = self.pk selected record excluded
    # for year > selecte record previous records are uploaded as start_year_string, record to new object
    # then using min function and lambda function only recent nearest immediate FY record is extracted 
    # --------------------------------------------------

    def get_next_year_record(self, lock=False):

        if not self.OLT_id:
            return None

        current_year = self.get_year_start(self.financial_Year)

        records = OLTInfraCharges.objects.filter(
            OLT_id=self.OLT_id
        )

        if self.pk:
            records = records.exclude(pk=self.pk)

        if lock:
            records = records.select_for_update()

        next_records = []

        for record in records:
            try:
                year = self.get_year_start(record.financial_Year)

                if year > current_year:
                    next_records.append((year, record))

            except ValueError:
                continue

        if not next_records:
            return None

        return min(next_records, key=lambda x: x[0])[1]

    # --------------------------------------------------
    # 6. VALIDATION AND AUTOMATIC PREVIOUS DUES use clean() method
    # if OLT is located in BSNL Premises then raise validation error 
    # validate Financial year string for consistancy
    # Waiver should not be more than applicable charges in all 3 cases else raise validation error
    # if creating new FY record self.pk is none then get previous record amount balance and assign it to self.previous_dues
    # --------------------------------------------------

    def clean(self):

        super().clean()

        # --------------------------------------------------
        # 1. Validate OLT location
        # --------------------------------------------------

        if self.OLT_id and self.OLT.located_at != 'BSNL premises':

            raise ValidationError({
                'OLT': (
                    "Infra charges are applicable only for "
                    "OLTs located in BSNL premises."
                )
            })

        # --------------------------------------------------
        # 2. Validate Financial Year
        # --------------------------------------------------

        try:
            self.get_year_start(self.financial_Year)

        except (ValueError, TypeError, ValidationError):
            raise ValidationError({
                'financial_Year': (
                    "Enter a valid financial year, e.g. 2025-26."
                )
            })

        # --------------------------------------------------
        # 3. Validate Waivers
        # --------------------------------------------------

        if self.infraChargesWaiver > self.applicableInfraCharges:

            raise ValidationError({
                'infraChargesWaiver': (
                    "Waiver cannot exceed Infra Charges."
                )
            })

        if self.securityDepositWaiver > self.applicableSecurityDeposit:

            raise ValidationError({
                'securityDepositWaiver': (
                    "Waiver cannot exceed Security Deposit."
                )
            })

        if self.oneTimeChargesWaiver > self.applicableOneTimeCharges:

            raise ValidationError({
                'oneTimeChargesWaiver': (
                    "Waiver cannot exceed One Time Charges."
                )
            })

        # --------------------------------------------------
        # 4. Automatically calculate Previous Dues
        #    ONLY when creating a new FY record
        # --------------------------------------------------

        if self.pk is None and self.OLT_id:

            previous_record = self.get_previous_year_record()

            if previous_record:
                self.previous_dues = previous_record.amount_Balance
            else:
                self.previous_dues = 0

    
    
    
    
    def _recalculate_balance_chain(self, records, *args, **kwargs):

        # Sort all records in ascending financial year order
        records = sorted(
            records,
            key=lambda x: x.get_year_start(x.financial_Year)
        )

        # First available FY always starts with zero previous dues
        previous_balance = 0

        for record in records:

            # --------------------------------------------------
            # 1. Set previous dues from preceding FY balance
            # --------------------------------------------------

            record.previous_dues = previous_balance

            # --------------------------------------------------
            # 2. Recalculate applicable charges
            # --------------------------------------------------

            record.total_Applicable_Charges_This_Year = (
                record.CalculateApplicableChargesThisYear()
            )

            # --------------------------------------------------
            # 3. Recalculate closing balance
            # --------------------------------------------------

            record.amount_Balance = (
                record.Calculate_Amount_Balance()
            )

            # --------------------------------------------------
            # 4. Save the record without calling overridden save()
            # --------------------------------------------------

            if record.pk == self.pk:

                # Current record: retain original save arguments
                save_kwargs = kwargs.copy()

                # Ensure calculated fields are included in update_fields
                if save_kwargs.get('update_fields') is not None:

                    update_fields = set(save_kwargs['update_fields'])

                    update_fields.update([
                        'previous_dues',
                        'total_Applicable_Charges_This_Year',
                        'amount_Balance',
                    ])

                    save_kwargs['update_fields'] = update_fields

                models.Model.save(
                    record,
                    *args,
                    **save_kwargs
                )

            else:

                # Subsequent records: save recalculated values
                models.Model.save(
                    record,
                    update_fields=[
                        'previous_dues',
                        'total_Applicable_Charges_This_Year',
                        'amount_Balance',
                    ]
                )

            # --------------------------------------------------
            # 5. Carry current closing balance to next FY
            # --------------------------------------------------

            previous_balance = record.amount_Balance
        
        
        
    
    
    
    # --------------------------------------------------
    # 7. SAVE METHOD - NEW RECORD AND UPDATE
    # a.  
    # --------------------------------------------------

    def save(self, *args, **kwargs):

        with transaction.atomic():

            # Lock OLT row to prevent simultaneous financial updates
            OLT.objects.select_for_update().get(pk=self.OLT_id)

            is_new = self.pk is None

            # Lock and retrieve existing record if updating
            if not is_new:

                old_instance = OLTInfraCharges.objects.select_for_update().get(
                    pk=self.pk
                )

                # OLT and FY cannot be changed after creation
                if (
                    old_instance.OLT_id != self.OLT_id
                    or old_instance.financial_Year != self.financial_Year
                ):
                    raise ValidationError(
                        "OLT and Financial Year cannot be changed "
                        "after the record has been created."
                    )

            # Calculate applicable charges
            self.total_Applicable_Charges_This_Year = (
                self.CalculateApplicableChargesThisYear()
            )

            # Previous dues are system-controlled.
            # Temporary value; actual value is assigned by chain recalculation.
            self.previous_dues = 0

            # Validate user-entered data
            self.full_clean()

            # Fetch and lock all other FY records belonging to this OLT
            existing_records = list(
                OLTInfraCharges.objects.select_for_update().filter(
                    OLT_id=self.OLT_id
                ).exclude(pk=self.pk)
            )

            # Include the current record in the chain
            all_records = existing_records + [self]

            # Recalculate current and all subsequent FY balances
            self._recalculate_balance_chain(
                all_records,
                *args,
                **kwargs
            )

    # --------------------------------------------------
    # 8. DELETE METHOD
    # --------------------------------------------------

    def delete(self, *args, **kwargs):

        with transaction.atomic():

            # Lock OLT row
            OLT.objects.select_for_update().get(pk=self.OLT_id)

            # Lock current record
            OLTInfraCharges.objects.select_for_update().get(pk=self.pk)

            # Delete current FY record without calling overridden delete()
            models.Model.delete(self, *args, **kwargs)

            # Fetch all remaining FY records for this OLT
            remaining_records = list(
                OLTInfraCharges.objects.select_for_update().filter(
                    OLT_id=self.OLT_id
                )
            )

            # Recalculate the entire remaining FY chain
            self._recalculate_balance_chain(remaining_records)



















"""
import re

from django.db import models, transaction
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class OLT(models.Model):

    LOCATION_CHOICES = [
        ('BSNL premises', 'BSNL premises'),
        ('Own premises', 'Own premises'),
    ]

    added_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='OLTs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    OLT_IP = models.GenericIPAddressField(unique=True)
    OA_Name = models.CharField(max_length=3)
    dateOfInstallation = models.DateField()
    franchisee_Name = models.CharField(max_length=50)
    located_at = models.CharField(
        max_length=20,
        choices=LOCATION_CHOICES
    )
    REM_ID = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.OLT_IP} - {self.OA_Name}"


class OLTInfraCharges(models.Model):

    OLT = models.ForeignKey(
        'OLT',
        on_delete=models.PROTECT,
        related_name="infra_charges"
    )

    financial_Year = models.CharField(
        max_length=7,
        help_text="Enter year like 2025-26"
    )

    previous_dues = models.IntegerField(default=0)

    applicableInfraCharges = models.IntegerField(default=0)
    applicableSecurityDeposit = models.IntegerField(default=0)
    applicableOneTimeCharges = models.IntegerField(default=0)

    infraChargesWaiver = models.IntegerField(default=0)
    securityDepositWaiver = models.IntegerField(default=0)
    oneTimeChargesWaiver = models.IntegerField(default=0)

    REM_Invoice_No = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    total_Applicable_Charges_This_Year = models.IntegerField(default=0)
    amount_Collected = models.IntegerField(default=0)
    amount_Balance = models.IntegerField(default=0)

    class Meta:
        unique_together = ('OLT', 'financial_Year')
        ordering = ['financial_Year']

    def __str__(self):
        return f"{self.OLT} - {self.financial_Year}"

    # --------------------------------------------------
    # 1. FINANCIAL YEAR VALIDATION - 
    #       a. It valdates vald string in financial_year entered by user
    #       b. returns 203 from string in case financial year is 2023-24
    # --------------------------------------------------

    @staticmethod
    def get_year_start(financial_year):

        match = re.fullmatch(r'(\d{4})-(\d{2})', financial_year or '')

        if not match:
            raise ValueError("Invalid Financial Year format")

        start_year = int(match.group(1))
        end_suffix = int(match.group(2))

        if end_suffix != (start_year + 1) % 100:
            raise ValueError("Invalid Financial Year")

        return start_year

    # --------------------------------------------------
    # 2. TOTAL CHARGES CALCULATION
    # --------------------------------------------------

    def CalculateApplicableChargesThisYear(self):

        infra_net = (
            self.applicableInfraCharges - self.infraChargesWaiver
        ) * 1.18

        security_net = (
            self.applicableSecurityDeposit - self.securityDepositWaiver
        )

        onetime_net = (
            self.applicableOneTimeCharges - self.oneTimeChargesWaiver
        ) * 1.18

        return int(infra_net + security_net + onetime_net)

    # --------------------------------------------------
    # 3. CLOSING BALANCE
    # --------------------------------------------------

    def Calculate_Amount_Balance(self):

        return (
            self.previous_dues
            + self.total_Applicable_Charges_This_Year
            - self.amount_Collected
        )

    # --------------------------------------------------
    # 4. FIND PREVIOUS FINANCIAL YEAR RECORD - 
    # $$$$$$$$here recnt previous record is collected$$$$$$$$
    # first for selected line to be modified or deleted start_year string is identified
    # then all records for self.olt_Id extracted from table OLT Infra Charges
    # then using pk = self.pk selected record excluded
    # for year < selecte record previous records are uploaded as start_year_string, record to new object
    # then using max function and lambda function only recent FY record is extracted 
    # --------------------------------------------------

    def get_previous_year_record(self, lock=False):

        if not self.OLT_id:             
            return None

        current_year = self.get_year_start(self.financial_Year) # returns 2023 in case fy = 2023-24
        # selectedYearStartString = self.get_year_start(self.financial_Year) # returns 2023

        # get all OLTInfraCharges rows/records for given OLT
        records = OLTInfraCharges.objects.filter(
            OLT_id=self.OLT_id
        )

        if self.pk:     # check if selected row/record has a primary key
            records = records.exclude(pk=self.pk) # filters out the current record from the database query results and saves in records  

        if lock:
            records = records.select_for_update()

        previous_records = []

        for record in records:
            try:
                year = self.get_year_start(record.financial_Year)

                if year < current_year:
                    previous_records.append((year, record))

            except ValueError:
                continue

        if not previous_records:
            return None

        return max(previous_records, key=lambda x: x[0])[1]
    

    # --------------------------------------------------
    # 5. FIND NEXT FINANCIAL YEAR RECORD
    # $$$$$$$$here immediate next record available is collected$$$$$$$$
    # first for selected line to be modified or deleted start_year string is identified
    # then all records for self.olt_Id extracted from table OLT Infra Charges
    # then using pk = self.pk selected record excluded
    # for year > selecte record previous records are uploaded as start_year_string, record to new object
    # then using min function and lambda function only recent nearest immediate FY record is extracted 
    # --------------------------------------------------

    def get_next_year_record(self, lock=False):

        if not self.OLT_id:
            return None

        current_year = self.get_year_start(self.financial_Year)

        records = OLTInfraCharges.objects.filter(
            OLT_id=self.OLT_id
        )

        if self.pk:
            records = records.exclude(pk=self.pk)

        if lock:
            records = records.select_for_update()

        next_records = []

        for record in records:
            try:
                year = self.get_year_start(record.financial_Year)

                if year > current_year:
                    next_records.append((year, record))

            except ValueError:
                continue

        if not next_records:
            return None

        return min(next_records, key=lambda x: x[0])[1]

    # --------------------------------------------------
    # 6. VALIDATION AND AUTOMATIC PREVIOUS DUES use clean() method
    # if OLT is located in BSNL Premises then raise validation error 
    # validate Financial year string for consistancy
    # Waiver should not be more than applicable charges in all 3 cases else raise validation error
    # if creating new FY record self.pk is none then get previous record amount balance and assign it to self.previous_dues
    # --------------------------------------------------

    def clean(self):

        super().clean()

        if self.OLT_id and self.OLT.located_at != 'BSNL premises':

            raise ValidationError({
                'OLT': (
                    "Infra charges are applicable only for "
                    "OLTs located in BSNL premises."
                )
            })
        #...............................
        try:
            self.get_year_start(self.financial_Year)

        except (ValueError, TypeError):
            raise ValidationError({
                'financial_Year': "Enter a valid financial year, e.g. 2025-26."
            })
        #...............................
        # Waivers cannot exceed the corresponding charges.

        if self.infraChargesWaiver > self.applicableInfraCharges:
            raise ValidationError({
                'infraChargesWaiver': "Waiver cannot exceed Infra Charges."
            })

        if self.securityDepositWaiver > self.applicableSecurityDeposit:
            raise ValidationError({
                'securityDepositWaiver': "Waiver cannot exceed Security Deposit."
            })

        if self.oneTimeChargesWaiver > self.applicableOneTimeCharges:
            raise ValidationError({
                'oneTimeChargesWaiver': "Waiver cannot exceed One Time Charges."
            })
        
        #...............................
        # creating a new financial year record.
        # Automatically collect previous year's closing balance. ONLY when creating a new financial year record.

        if self.pk is None and self.OLT_id:

            previous_record = self.get_previous_year_record()

            if previous_record:
                self.previous_dues = previous_record.amount_Balance

    # --------------------------------------------------
    # 7. SAVE METHOD - NEW RECORD AND UPDATE
    # a.  
    # --------------------------------------------------

    def save(self, *args, **kwargs):

        with transaction.atomic():
            # Lock the OLT row to serialize financial updates
            # belonging to the same OLT.

            if self.OLT_id:
                OLT.objects.select_for_update().get(pk=self.OLT_id)
            # Performs a database lock (SELECT ... FOR UPDATE) on the specific OLT row associated with this record. This prevents other concurrent threads or requests from modifying or reading/writing financial values for this specific OLT until the current transaction finishes, avoiding race conditions.
           
            #----------------------
            # self.pk is not None in case modifying or deleting old records
            old_balance = 0 
            is_new = self.pk is None  # self.pk is None only in case when new OLT record for any FY is getting added in sheet
            # Initializes a variable to track the previous balance of the record before any changes are saved, which is typically used right after to compare old and new financial values.

            if not is_new: # in case of old record is being updated
                old_instance = OLTInfraCharges.objects.select_for_update().get(
                    pk=self.pk
                )
                # Fetches the existing database record and applies a row-level lock (FOR UPDATE) on it. This ensures that no other database transaction can read or write to this specific row until your current transaction finishes, preventing race conditions if concurrent requests try to update the same financial record simultaneously.
                if ( 
                    old_instance.OLT_id != self.OLT_id
                    or old_instance.financial_Year != self.financial_Year
                ): raise ValidationError(
                        "OLT and Financial Year cannot be changed "
                        "after the record has been created."
                )  # Financial year and OLT should not be changed
                # after creation because that would break the chain.

                old_balance = old_instance.amount_Balance 
            #----------------------
            # Compute total applicable charges using the helper method (excluding previous dues)
            self.total_Applicable_Charges_This_Year = self.CalculateApplicableChargesThisYear()

            # Run all validations and calculate previous dues.

            self.full_clean()

            # For a new record, the previous closing balance is
            # the baseline already included in the next year's dues.
            # If no earlier record exists, preserve manually entered
            # opening dues as the baseline.

            # old_balance is captured to modify next financial year record
            # old_balance = 0 in case of new records
            # old_balance = Amount_balance of captured event before editing or modifying row
            if is_new:
                previous_record = self.get_previous_year_record(lock=True)
                if previous_record:
                    self.previous_dues = previous_record.amount_Balance
                else:
                    self.previous_dues = 0
            
            # Compute closing balance
            self.amount_Balance = self.Calculate_Amount_Balance()

            # Save current financial year.

            super().save(*args, **kwargs)

            # Find the next existing financial year.

            next_year_record = self.get_next_year_record(lock=True)

            if next_year_record:

                # Calculate the difference in closing balance.

                balance_delta = self.amount_Balance - old_balance

                if balance_delta != 0:

                    # Adjust next year's previous dues.

                    next_year_record.previous_dues += balance_delta

                    # Save next year.
                    # Its own save() propagates the adjustment
                    # to all subsequent financial years.

                    next_year_record.save()

    # --------------------------------------------------
    # 8. DELETE METHOD
    # --------------------------------------------------

    def delete(self, *args, **kwargs):

        with transaction.atomic():

            # Lock the OLT row.

            OLT.objects.select_for_update().get(pk=self.OLT_id)

            # Fetch latest database values under lock.

            OLTInfraCharges.objects.select_for_update().get(pk=self.pk)

            self.refresh_from_db()

            # Find the previous and next existing financial years.

            previous_record = self.get_previous_year_record(lock=True)

            next_year_record = self.get_next_year_record(lock=True)

            if next_year_record:
                
                if previous_record:
                    revised_previous_dues = previous_record.amount_Balance
                else:
                    revised_previous_dues = 0
                
                balance_delta = (revised_previous_dues - self.amount_Balance)

                next_year_record.previous_dues += balance_delta

                next_year_record.save()

            # Finally delete the current financial year record.

            super().delete(*args, **kwargs)"""


