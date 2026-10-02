from decimal import Decimal
from pathlib import Path
import uuid

from django.db import transaction
from django.urls import reverse
from rest_framework import serializers

from .models import (
    BillingRecord,
    Employee,
    EmployeeDocument,
    ExpenseCategory,
    ExpenseLineItem,
    ExpenseProduct,
    ExpenseRecord,
    HiringRecord,
)


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeDocument
        fields = ["id", "employee", "title", "category", "file", "download_url", "uploaded_at"]
        read_only_fields = ["id", "uploaded_at"]

    def get_download_url(self, instance):
        return reverse("employee-document-download", args=[instance.pk])

    def validate_file(self, value):
        allowed_extensions = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
        if Path(value.name).suffix.lower() not in allowed_extensions:
            raise serializers.ValidationError("Upload a PDF, image, or Word document.")
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("Files must be 10 MB or smaller.")
        return value


class EmployeeSerializer(serializers.ModelSerializer):
    documents = EmployeeDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_id",
            "full_name",
            "phone",
            "email",
            "nationality",
            "job_title",
            "client_name",
            "origin_country",
            "destination",
            "status",
            "documents",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HiringRecordSerializer(serializers.ModelSerializer):
    employee = serializers.PrimaryKeyRelatedField(
        queryset=Employee.objects.all(),
        required=False,
        allow_null=True,
    )
    applicant_name = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=160)
    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_id = serializers.CharField(source="employee.employee_id", read_only=True)
    client_name = serializers.CharField(required=False, allow_blank=True)
    hiring_person_name = serializers.CharField(required=False, allow_blank=True)
    passport_photo = serializers.FileField(write_only=True, required=False)
    passport_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = HiringRecord
        fields = [
            "id",
            "employee",
            "applicant_name",
            "employee_id",
            "employee_name",
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
            "passport_photo_url",
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
            "created_at",
        ]
        read_only_fields = ["id", "employee_id", "employee_name", "passport_photo_url", "created_at"]

    def get_passport_photo_url(self, instance):
        if not instance.passport_photo:
            return ""
        return reverse("joining-photo", args=[instance.pk])

    def validate_passport_photo(self, value):
        allowed_extensions = {".jpg", ".jpeg", ".png"}
        if Path(value.name).suffix.lower() not in allowed_extensions:
            raise serializers.ValidationError("Upload a JPG or PNG passport photo.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Passport photos must be 5 MB or smaller.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        applicant_name = validated_data.pop("applicant_name", "").strip()
        employee = validated_data.get("employee")
        client_name = validated_data.get("client_name") or (employee.client_name if employee else "")
        validated_data["client_name"] = client_name
        request_user = self.context["request"].user
        validated_data["hiring_person_name"] = (
            validated_data.get("hiring_person_name")
            or validated_data.get("hr_name")
            or request_user.get_full_name()
            or request_user.get_username()
        )
        if employee is None:
            if not applicant_name:
                raise serializers.ValidationError({"applicant_name": "Enter a name or link an existing employee."})
            employee_number = validated_data.get("assigned_employee_number")
            if employee_number and Employee.objects.filter(employee_id=employee_number).exists():
                raise serializers.ValidationError({"assigned_employee_number": "This employee number is already in use."})
            employee = Employee.objects.create(
                employee_id=employee_number or f"JOIN-{uuid.uuid4().hex[:12].upper()}",
                full_name=applicant_name,
                phone=validated_data.get("mobile_number", ""),
                nationality=validated_data.get("nationality", ""),
                job_title=validated_data.get("job_title", ""),
                client_name=client_name,
                created_by=request_user,
            )
            validated_data["employee"] = employee
        return super().create(validated_data)


class BillingRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.full_name", read_only=True, allow_null=True)

    class Meta:
        model = BillingRecord
        fields = [
            "id",
            "invoice_number",
            "client_name",
            "employee",
            "employee_name",
            "description",
            "amount",
            "currency",
            "bill_date",
            "status",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "employee_name", "created_at"]


class ExpenseLineItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=ExpenseProduct.objects.all())
    product_name = serializers.CharField(read_only=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal("0.01"))
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ExpenseLineItem
        fields = ["id", "product", "product_name", "quantity", "unit_price", "line_total"]
        read_only_fields = ["id", "product_name", "unit_price", "line_total"]


class ExpenseRecordSerializer(serializers.ModelSerializer):
    items = ExpenseLineItemSerializer(many=True, required=False)

    class Meta:
        model = ExpenseRecord
        fields = [
            "id",
            "reference_number",
            "vendor_name",
            "category",
            "description",
            "amount",
            "currency",
            "bill_date",
            "due_date",
            "paid_date",
            "status",
            "notes",
            "items",
            "created_at",
        ]
        read_only_fields = ["id", "category", "description", "amount", "currency", "created_at"]

    def validate_items(self, items):
        currencies = {item["product"].currency for item in items}
        if len(currencies) > 1:
            raise serializers.ValidationError("All products on a bill must use the same currency.")
        return items

    @staticmethod
    def _line_totals(items):
        lines = []
        amount = Decimal("0.00")
        for item in items:
            product = item["product"]
            quantity = item["quantity"]
            line_total = (quantity * product.unit_price).quantize(Decimal("0.01"))
            amount += line_total
            lines.append({
                "product": product,
                "product_name": product.name,
                "quantity": quantity,
                "unit_price": product.unit_price,
                "line_total": line_total,
            })
        return lines, amount

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items", [])
        if not items:
            raise serializers.ValidationError({"items": "Add at least one product to the bill."})
        lines, amount = self._line_totals(items)
        validated_data["amount"] = amount
        validated_data["currency"] = items[0]["product"].currency
        validated_data["category"] = ", ".join(sorted({
            item["product"].category.name for item in items
        }))[:80]
        validated_data["description"] = ", ".join(line["product_name"] for line in lines)[:240]
        expense = ExpenseRecord.objects.create(**validated_data)
        ExpenseLineItem.objects.bulk_create([
            ExpenseLineItem(expense=expense, **line) for line in lines
        ])
        return expense

    @transaction.atomic
    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if items is not None:
            if not items:
                raise serializers.ValidationError({"items": "Add at least one product to the bill."})
            lines, instance.amount = self._line_totals(items)
            instance.currency = items[0]["product"].currency
            instance.category = ", ".join(sorted({
                item["product"].category.name for item in items
            }))[:80]
            instance.description = ", ".join(line["product_name"] for line in lines)[:240]
            instance.items.all().delete()
            ExpenseLineItem.objects.bulk_create([
                ExpenseLineItem(expense=instance, **line) for line in lines
            ])
        instance.save()
        return instance


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = ["id", "name"]
        read_only_fields = ["id"]


class ExpenseProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = ExpenseProduct
        fields = ["id", "name", "category", "category_name", "unit_price", "currency"]
        read_only_fields = ["id", "category_name"]