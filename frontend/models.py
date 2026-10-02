import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def employee_document_upload_path(instance, filename):
	suffix = Path(filename).suffix.lower()
	return f"employee_documents/{uuid.uuid4().hex}{suffix}"


def joining_photo_upload_path(instance, filename):
	suffix = Path(filename).suffix.lower()
	return f"joining_photos/{uuid.uuid4().hex}{suffix}"


class Employee(models.Model):
	class Status(models.TextChoices):
		ACTIVE = "active", "Active"
		PENDING = "pending", "Pending"
		ON_LEAVE = "on_leave", "On leave"
		COMPLETED = "completed", "Completed"

	employee_id = models.CharField(max_length=32, unique=True)
	full_name = models.CharField(max_length=160)
	phone = models.CharField(max_length=32)
	email = models.EmailField(blank=True)
	nationality = models.CharField(max_length=80, blank=True)
	job_title = models.CharField(max_length=120, blank=True)
	client_name = models.CharField(max_length=160, blank=True)
	origin_country = models.CharField(max_length=80, default="Nepal")
	destination = models.CharField(max_length=100, default="Dubai, UAE")
	status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
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


class HiringRecord(models.Model):
	class Status(models.TextChoices):
		NEW = "new", "New"
		IN_PROGRESS = "in_progress", "In progress"
		CONFIRMED = "confirmed", "Confirmed"
		ARRIVED = "arrived", "Arrived"

	employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="joinings")
	client_name = models.CharField(max_length=160)
	hiring_person_name = models.CharField(max_length=160)
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
		return f"{self.employee} joining {self.client_name}"


class EmployeeDocument(models.Model):
	class Category(models.TextChoices):
		PASSPORT = "passport", "Passport"
		PHOTO = "photo", "Photo"
		CONTRACT = "contract", "Contract"
		OTHER = "other", "Other"

	employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="documents")
	title = models.CharField(max_length=120)
	category = models.CharField(max_length=16, choices=Category.choices, default=Category.OTHER)
	file = models.FileField(upload_to=employee_document_upload_path)
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


class BillingRecord(models.Model):
	class Status(models.TextChoices):
		DRAFT = "draft", "Draft"
		SENT = "sent", "Sent"
		PAID = "paid", "Paid"
		OVERDUE = "overdue", "Overdue"

	invoice_number = models.CharField(max_length=40, unique=True)
	client_name = models.CharField(max_length=160)
	employee = models.ForeignKey(
		Employee,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="billing_records",
	)
	description = models.CharField(max_length=240)
	amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
	currency = models.CharField(max_length=3, default="AED")
	bill_date = models.DateField()
	status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
	notes = models.TextField(blank=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="created_billing_records",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-bill_date", "invoice_number"]

	def __str__(self):
		return f"{self.invoice_number} - {self.client_name}"


class ExpenseRecord(models.Model):
	class Status(models.TextChoices):
		UNPAID = "unpaid", "Unpaid"
		PAID = "paid", "Paid"
		OVERDUE = "overdue", "Overdue"

	reference_number = models.CharField(max_length=40, blank=True)
	vendor_name = models.CharField(max_length=160)
	category = models.CharField(max_length=80)
	description = models.CharField(max_length=240, blank=True)
	amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
	currency = models.CharField(max_length=3, default="AED")
	bill_date = models.DateField()
	due_date = models.DateField(null=True, blank=True)
	paid_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=12, choices=Status.choices, default=Status.UNPAID)
	notes = models.TextField(blank=True)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="created_expense_records",
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-bill_date", "vendor_name"]

	def __str__(self):
		return f"{self.vendor_name} - {self.amount} {self.currency}"


class ExpenseCategory(models.Model):
	name = models.CharField(max_length=80, unique=True)

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
