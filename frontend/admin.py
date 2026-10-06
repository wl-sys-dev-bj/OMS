from django.contrib import admin
from .models import (
    AuditLog,
    BillingRecord,
    Department,
    Designation,
    Employee,
    EmployeeDocument,
    ExpenseCategory,
    ExpenseLineItem,
    ExpenseProduct,
    ExpenseRecord,
    HiringRecord,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "phone"]
    list_filter = ["role"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "user__email", "phone"]


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "employee_count", "created_at"]
    search_fields = ["name", "code", "description"]

    def employee_count(self, obj):
        return obj.employees.count()
    employee_count.short_description = "Employees"


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ["name", "department", "created_at"]
    list_filter = ["department"]
    search_fields = ["name", "description"]


class EmployeeDocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 0
    readonly_fields = ["uploaded_at"]


class HiringRecordInline(admin.StackedInline):
    model = HiringRecord
    extra = 0
    readonly_fields = ["created_at"]


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["employee_id", "full_name", "phone", "email", "department", "designation", "status", "client_name"]
    list_filter = ["status", "employment_type", "department", "work_location", "nationality"]
    search_fields = ["employee_id", "full_name", "phone", "email", "passport_number", "citizenship_number", "client_name"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [EmployeeDocumentInline, HiringRecordInline]
    fieldsets = (
        ("Core Identification", {
            "fields": ("employee_id", "first_name", "middle_name", "last_name", "full_name", "profile_photo")
        }),
        ("Personal Information", {
            "fields": ("date_of_birth", "gender", "nationality", "marital_status")
        }),
        ("Contact Information", {
            "fields": ("phone", "email", "emergency_contact_name", "emergency_contact_relationship", "emergency_contact_phone", "current_address", "permanent_address")
        }),
        ("Employment Information", {
            "fields": ("department", "designation", "job_title", "employment_type", "joining_date", "contract_start_date", "contract_end_date", "salary", "status", "supervisor", "work_location", "client_name", "origin_country", "destination")
        }),
        ("Official Identification", {
            "fields": ("citizenship_number", "passport_number", "pan_tax_number", "national_id_number")
        }),
        ("Audit Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(HiringRecord)
class HiringRecordAdmin(admin.ModelAdmin):
    list_display = ["employee", "client_name", "joining_date", "hiring_person_name", "status"]
    list_filter = ["status", "joining_date", "nationality"]
    search_fields = ["employee__full_name", "employee__employee_id", "client_name", "passport_number", "citizenship_number"]
    readonly_fields = ["created_at"]


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "employee", "category", "uploaded_by", "uploaded_at"]
    list_filter = ["category", "uploaded_at"]
    search_fields = ["title", "employee__full_name", "employee__employee_id"]
    readonly_fields = ["uploaded_at"]


class ExpenseLineItemInline(admin.TabularInline):
    model = ExpenseLineItem
    extra = 0
    readonly_fields = ["line_total"]


@admin.register(ExpenseRecord)
class ExpenseRecordAdmin(admin.ModelAdmin):
    list_display = ["reference_number", "vendor_name", "employee", "category", "amount", "currency", "bill_date", "status", "payment_method"]
    list_filter = ["status", "payment_method", "bill_date", "category_ref", "department"]
    search_fields = ["reference_number", "vendor_name", "description", "invoice_number", "employee__full_name"]
    readonly_fields = ["created_at", "updated_at", "approved_at"]
    inlines = [ExpenseLineItemInline]


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "description"]
    search_fields = ["name", "description"]


@admin.register(ExpenseProduct)
class ExpenseProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "unit_price", "currency"]
    list_filter = ["category", "currency"]
    search_fields = ["name", "category__name"]


@admin.register(BillingRecord)
class BillingRecordAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "client_name", "amount", "currency", "bill_date", "status"]
    list_filter = ["status", "bill_date", "currency"]
    search_fields = ["invoice_number", "client_name", "description"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "user", "action", "model_name", "object_repr", "ip_address"]
    list_filter = ["action", "model_name", "timestamp"]
    search_fields = ["object_repr", "object_id", "changes", "user__username"]
    readonly_fields = ["timestamp", "user", "action", "model_name", "object_id", "object_repr", "changes", "ip_address"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
