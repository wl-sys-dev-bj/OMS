from decimal import Decimal
from pathlib import Path
from django import forms
from django.core.exceptions import ValidationError
from frontend.models import (
    Employee,
    HiringRecord,
    EmployeeDocument,
    ExpenseRecord,
    ExpenseCategory,
    ExpenseProduct,
    BillingRecord,
    Department,
    Designation,
)


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "employee_id",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "nationality",
            "marital_status",
            "profile_photo",
            "phone",
            "email",
            "emergency_contact_name",
            "emergency_contact_relationship",
            "emergency_contact_phone",
            "current_address",
            "permanent_address",
            "department",
            "designation",
            "job_title",
            "employment_type",
            "joining_date",
            "contract_start_date",
            "contract_end_date",
            "salary",
            "status",
            "supervisor",
            "work_location",
            "client_name",
            "origin_country",
            "destination",
            "citizenship_number",
            "passport_number",
            "pan_tax_number",
            "national_id_number",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "joining_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "contract_start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "contract_end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "current_address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
            "permanent_address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def clean_employee_id(self):
        emp_id = self.cleaned_data.get("employee_id", "").strip()
        if not emp_id:
            raise ValidationError("Employee ID is required.")
        qs = Employee.objects.filter(employee_id__iexact=emp_id)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Employee ID '{emp_id}' is already assigned to another employee.")
        return emp_id

    def clean_salary(self):
        salary = self.cleaned_data.get("salary")
        if salary is not None and salary < 0:
            raise ValidationError("Salary amount cannot be negative.")
        return salary

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("contract_start_date")
        end = cleaned_data.get("contract_end_date")
        if start and end and end < start:
            self.add_error("contract_end_date", "Contract end date cannot be before contract start date.")
        return cleaned_data


class HiringRecordForm(forms.ModelForm):
    applicant_name = forms.CharField(max_length=160, required=False)

    class Meta:
        model = HiringRecord
        fields = [
            "employee",
            "applicant_name",
            "client_name",
            "hiring_person_name",
            "hiring_person_employee_id",
            "application_date",
            "joining_date",
            "father_name",
            "nationality",
            "city",
            "visa_status",
            "visa_expiry",
            "passport_number",
            "citizenship_number",
            "passport_expiry",
            "passport_photo",
            "mobile_number",
            "secondary_mobile_number",
            "whatsapp_number",
            "secondary_whatsapp_number",
            "home_number",
            "secondary_home_number",
            "basic_salary",
            "commission_percent",
            "allowance",
            "room_provided",
            "training_period",
            "starting_date",
            "end_date",
            "monthly_target",
            "visa_charges",
            "job_title",
            "hr_name",
            "hr_phone",
            "assigned_employee_number",
            "destination",
            "status",
            "notes",
        ]
        widgets = {
            "application_date": forms.DateInput(attrs={"type": "date"}),
            "joining_date": forms.DateInput(attrs={"type": "date"}),
            "visa_expiry": forms.DateInput(attrs={"type": "date"}),
            "passport_expiry": forms.DateInput(attrs={"type": "date"}),
            "starting_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_passport_photo(self):
        photo = self.cleaned_data.get("passport_photo")
        if photo and hasattr(photo, "name"):
            ext = Path(photo.name).suffix.lower()
            if ext not in [".jpg", ".jpeg", ".png"]:
                raise ValidationError("Passport photo must be a JPG or PNG image.")
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError("Passport photo cannot exceed 5 MB.")
        return photo


class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        fields = ["title", "category", "file", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        if uploaded_file:
            allowed = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
            ext = Path(uploaded_file.name).suffix.lower()
            if ext not in allowed:
                raise ValidationError("Allowed document formats: PDF, JPG, PNG, DOC, DOCX.")
            if uploaded_file.size > 10 * 1024 * 1024:
                raise ValidationError("File size cannot exceed 10 MB.")
        return uploaded_file


class ExpenseRecordForm(forms.ModelForm):
    class Meta:
        model = ExpenseRecord
        fields = [
            "reference_number",
            "employee",
            "department",
            "category_ref",
            "category",
            "vendor_name",
            "description",
            "amount",
            "currency",
            "bill_date",
            "due_date",
            "paid_date",
            "payment_method",
            "invoice_number",
            "status",
            "receipt_file",
            "invoice_file",
            "notes",
        ]
        widgets = {
            "bill_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "paid_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount < 0:
            raise ValidationError("Expense amount cannot be negative.")
        return amount

    def clean_receipt_file(self):
        receipt = self.cleaned_data.get("receipt_file")
        if receipt and hasattr(receipt, "name"):
            allowed = {".pdf", ".jpg", ".jpeg", ".png"}
            ext = Path(receipt.name).suffix.lower()
            if ext not in allowed:
                raise ValidationError("Receipt must be PDF, JPG, or PNG.")
            if receipt.size > 10 * 1024 * 1024:
                raise ValidationError("Receipt file cannot exceed 10 MB.")
        return receipt


class BillingRecordForm(forms.ModelForm):
    class Meta:
        model = BillingRecord
        fields = [
            "invoice_number",
            "client_name",
            "employee",
            "description",
            "amount_before_tax",
            "tax_amount",
            "amount",
            "currency",
            "bill_date",
            "due_date",
            "payment_date",
            "status",
            "attachment",
            "notes",
        ]
        widgets = {
            "bill_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount < 0:
            raise ValidationError("Invoice amount cannot be negative.")
        return amount


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "code", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designation
        fields = ["name", "department", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["name", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
        }


class ExpenseProductForm(forms.ModelForm):
    class Meta:
        model = ExpenseProduct
        fields = ["name", "category", "unit_price", "currency"]
