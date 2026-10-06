import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


def employee_document_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"employee_documents/{uuid.uuid4().hex}{suffix}"


def employee_photo_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"employee_photos/{uuid.uuid4().hex}{suffix}"


def joining_photo_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"joining_photos/{uuid.uuid4().hex}{suffix}"


def expense_receipt_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"expense_receipts/{uuid.uuid4().hex}{suffix}"


def expense_invoice_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"expense_invoices/{uuid.uuid4().hex}{suffix}"


def billing_document_upload_path(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"billing_documents/{uuid.uuid4().hex}{suffix}"


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrator"
        HR = "hr", "HR Specialist"
        FINANCE = "finance", "Finance & Accounts"
        MANAGER = "manager", "Operations Manager"
        EMPLOYEE = "employee", "Standard Employee"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ADMIN)
    phone = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.user.is_superuser

    @property
    def is_hr(self):
        return self.role in (self.Role.ADMIN, self.Role.HR) or self.user.is_superuser

    @property
    def is_finance(self):
        return self.role in (self.Role.ADMIN, self.Role.FINANCE) or self.user.is_superuser

    @property
    def is_manager(self):
        return self.role in (self.Role.ADMIN, self.Role.MANAGER, self.Role.HR) or self.user.is_superuser


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        role = UserProfile.Role.ADMIN if instance.is_superuser else UserProfile.Role.EMPLOYEE
        UserProfile.objects.get_or_create(user=instance, defaults={"role": role})


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Designation(models.Model):
    name = models.CharField(max_length=120, unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="designations",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Employee(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending"
        ON_LEAVE = "on_leave", "On leave"
        SUSPENDED = "suspended", "Suspended"
        RESIGNED = "resigned", "Resigned"
        TERMINATED = "terminated", "Terminated"
        RETIRED = "retired", "Retired"
        COMPLETED = "completed", "Completed"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    class MaritalStatus(models.TextChoices):
        SINGLE = "single", "Single"
        MARRIED = "married", "Married"
        DIVORCED = "divorced", "Divorced"
        WIDOWED = "widowed", "Widowed"
        OTHER = "other", "Other"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        CONTRACT = "contract", "Contract"
        PROBATION = "probation", "Probation"
        TEMPORARY = "temporary", "Temporary"
        INTERN = "intern", "Intern"

    # Core identification
    employee_id = models.CharField(max_length=32, unique=True, db_index=True)
    first_name = models.CharField(max_length=80, blank=True)
    middle_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)
    full_name = models.CharField(max_length=160, db_index=True)

    # Personal details
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=16, choices=Gender.choices, blank=True)
    nationality = models.CharField(max_length=80, blank=True, default="Nepali")
    marital_status = models.CharField(max_length=16, choices=MaritalStatus.choices, blank=True)
    profile_photo = models.FileField(upload_to=employee_photo_upload_path, blank=True)

    # Contact details
    phone = models.CharField(max_length=32, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    emergency_contact_name = models.CharField(max_length=160, blank=True)
    emergency_contact_relationship = models.CharField(max_length=80, blank=True)
    emergency_contact_phone = models.CharField(max_length=32, blank=True)
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)

    # Employment details
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
    )
    job_title = models.CharField(max_length=120, blank=True)
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )
    joining_date = models.DateField(null=True, blank=True)
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    supervisor = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subordinates",
    )
    work_location = models.CharField(max_length=120, blank=True, default="Dubai, UAE")
    client_name = models.CharField(max_length=160, blank=True)
    origin_country = models.CharField(max_length=80, default="Nepal", blank=True)
    destination = models.CharField(max_length=100, default="Dubai, UAE", blank=True)

    # Official identification numbers
    citizenship_number = models.CharField(max_length=60, blank=True)
    passport_number = models.CharField(max_length=60, blank=True)
    pan_tax_number = models.CharField(max_length=60, blank=True)
    national_id_number = models.CharField(max_length=60, blank=True)

    # Metadata & Tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_employees",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["full_name", "employee_id"]

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"

    def save(self, *args, **kwargs):
        # Auto-compute full_name if first_name is given
        if self.first_name and not self.full_name:
            parts = [self.first_name, self.middle_name, self.last_name]
            self.full_name = " ".join(part.strip() for part in parts if part.strip())
        elif self.full_name and not self.first_name:
            parts = self.full_name.strip().split()
            if parts:
                self.first_name = parts[0]
                if len(parts) > 1:
                    self.last_name = parts[-1]
                if len(parts) > 2:
                    self.middle_name = " ".join(parts[1:-1])
        super().save(*args, **kwargs)


class HiringRecord(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        CONFIRMED = "confirmed", "Confirmed"
        ARRIVED = "arrived", "Arrived"

    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="joinings")
    client_name = models.CharField(max_length=160, blank=True)
    hiring_person_name = models.CharField(max_length=160, blank=True)
    hiring_person_employee_id = models.CharField(max_length=32, blank=True)
    application_date = models.DateField(null=True, blank=True)
    joining_date = models.DateField()
    father_name = models.CharField(max_length=160, blank=True)
    nationality = models.CharField(max_length=80, blank=True)
    city = models.CharField(max_length=100, blank=True)
    visa_status = models.CharField(max_length=40, blank=True)
    visa_expiry = models.DateField(null=True, blank=True)
    passport_number = models.CharField(max_length=40, blank=True)
    citizenship_number = models.CharField(max_length=40, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)
    passport_photo = models.FileField(upload_to=joining_photo_upload_path, blank=True)
    mobile_number = models.CharField(max_length=32, blank=True)
    secondary_mobile_number = models.CharField(max_length=32, blank=True)
    whatsapp_number = models.CharField(max_length=32, blank=True)
    secondary_whatsapp_number = models.CharField(max_length=32, blank=True)
    home_number = models.CharField(max_length=32, blank=True)
    secondary_home_number = models.CharField(max_length=32, blank=True)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    allowance = models.CharField(max_length=160, blank=True)
    room_provided = models.BooleanField(default=False)
    training_period = models.CharField(max_length=80, blank=True)
    starting_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    monthly_target = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    visa_charges = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    job_title = models.CharField(max_length=120, blank=True)
    hr_name = models.CharField(max_length=160, blank=True)
    hr_phone = models.CharField(max_length=32, blank=True)
    assigned_employee_number = models.CharField(max_length=32, blank=True)
    destination = models.CharField(max_length=100, default="Dubai, UAE")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_hiring_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-joining_date", "-created_at"]

    def __str__(self):
        return f"{self.employee} joining {self.client_name or 'Unassigned'}"


class EmployeeDocument(models.Model):
    class Category(models.TextChoices):
        PASSPORT = "passport", "Passport"
        PHOTO = "photo", "Photo"
        CONTRACT = "contract", "Contract"
        VISA = "visa", "Visa"
        CERTIFICATE = "certificate", "Certificate"
        ID_CARD = "id_card", "ID Card"
        OTHER = "other", "Other"

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    file = models.FileField(upload_to=employee_document_upload_path)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_employee_documents",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.title} ({self.employee.employee_id})"


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "expense categories"

    def __str__(self):
        return self.name


class ExpenseProduct(models.Model):
    name = models.CharField(max_length=160)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name="products")
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField(max_length=3, default="AED")

    class Meta:
        ordering = ["category__name", "name"]

    def __str__(self):
        return self.name


class ExpenseRecord(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        UNPAID = "unpaid", "Unpaid"
        OVERDUE = "overdue", "Overdue"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CREDIT_CARD = "credit_card", "Credit Card"
        DEBIT_CARD = "debit_card", "Debit Card"
        CHEQUE = "cheque", "Cheque"
        ONLINE = "online", "Online Payment"
        OTHER = "other", "Other"

    reference_number = models.CharField(max_length=60, blank=True, db_index=True)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
    )
    category_ref = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expense_records",
    )
    category = models.CharField(max_length=120, blank=True)
    vendor_name = models.CharField(max_length=160, blank=True)
    description = models.CharField(max_length=240, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="AED")
    bill_date = models.DateField(db_index=True)
    due_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    invoice_number = models.CharField(max_length=60, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    receipt_file = models.FileField(upload_to=expense_receipt_upload_path, blank=True)
    invoice_file = models.FileField(upload_to=expense_invoice_upload_path, blank=True)
    notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_expenses",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_expense_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-bill_date", "-created_at"]

    def __str__(self):
        return f"{self.reference_number or self.vendor_name or 'Expense'} - {self.amount} {self.currency}"

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"EXP-{uuid.uuid4().hex[:8].upper()}"
        if self.category_ref and not self.category:
            self.category = self.category_ref.name
        super().save(*args, **kwargs)


class ExpenseLineItem(models.Model):
    expense = models.ForeignKey(ExpenseRecord, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        ExpenseProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bill_items",
    )
    product_name = models.CharField(max_length=160)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"


class BillingRecord(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"

    invoice_number = models.CharField(max_length=60, unique=True, db_index=True)
    client_name = models.CharField(max_length=160, db_index=True)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="billing_records",
    )
    description = models.CharField(max_length=240)
    amount_before_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default="AED")
    bill_date = models.DateField(db_index=True)
    due_date = models.DateField(null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    attachment = models.FileField(upload_to=billing_document_upload_path, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_billing_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-bill_date", "invoice_number"]

    def __str__(self):
        return f"{self.invoice_number} - {self.client_name}"


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Created"
        UPDATE = "update", "Updated"
        DELETE = "delete", "Deleted"
        APPROVE = "approve", "Approved"
        REJECT = "reject", "Rejected"
        MARK_PAID = "mark_paid", "Marked as Paid"
        UPLOAD = "upload", "Uploaded Document"
        EXPORT = "export", "Exported Data"
        PRINT = "print", "Printed Record"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    model_name = models.CharField(max_length=60)
    object_id = models.CharField(max_length=60, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    changes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user} - {self.get_action_display()} {self.model_name} #{self.object_id}"
