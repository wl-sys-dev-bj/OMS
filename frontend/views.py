import mimetypes
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from rest_framework import permissions, status as http_status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .forms import (
    BillingRecordForm,
    DepartmentForm,
    DesignationForm,
    EmployeeDocumentForm,
    EmployeeForm,
    ExpenseCategoryForm,
    ExpenseProductForm,
    ExpenseRecordForm,
    HiringRecordForm,
)
from .models import (
    AuditLog,
    BillingRecord,
    Department,
    Designation,
    Employee,
    EmployeeDocument,
    ExpenseCategory,
    ExpenseProduct,
    ExpenseRecord,
    HiringRecord,
    UserProfile,
)
from .permissions import (
    CanApproveExpenses,
    CanManageEmployees,
    CanManageExpenses,
    finance_or_admin_required,
    hr_or_admin_required,
    manager_or_above_required,
    role_required,
)
from .serializers import (
    AuditLogSerializer,
    BillingRecordSerializer,
    DepartmentSerializer,
    DesignationSerializer,
    EmployeeDocumentSerializer,
    EmployeeSerializer,
    ExpenseCategorySerializer,
    ExpenseProductSerializer,
    ExpenseRecordSerializer,
    HiringRecordSerializer,
)
from .services.audit_service import log_action
from .services.export_service import (
    export_employees_csv,
    export_employees_excel,
    export_expenses_csv,
    export_expenses_excel,
)
from .services.pdf_service import (
    generate_employee_pdf,
    generate_employee_report_pdf,
    generate_expense_pdf,
    generate_expense_report_pdf,
    generate_joining_pdf,
)


# ==========================================
# AUTHENTICATION VIEWS
# ==========================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, "login.html")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            log_action(user, AuditLog.Action.UPDATE, user, "User logged in", request)
            next_url = request.GET.get("next") or "home"
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "login.html")

    return render(request, "login.html")


def logout_view(request):
    if request.user.is_authenticated:
        log_action(request.user, AuditLog.Action.UPDATE, request.user, "User logged out", request)
    logout(request)
    return redirect("login")


# ==========================================
# DASHBOARD & OVERVIEW
# ==========================================

@login_required(login_url="login")
def home(request):
    """Main operations workspace & dashboard."""
    return render(request, "dashboard.html")


@login_required(login_url="login")
def dashboard_stats_api(request):
    """API endpoint providing real-time aggregates for the dashboard."""
    now = timezone.now()
    first_day_of_month = date(now.year, now.month, 1)

    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(status=Employee.Status.ACTIVE).count()
    inactive_employees = Employee.objects.exclude(status=Employee.Status.ACTIVE).count()
    new_this_month = Employee.objects.filter(created_at__gte=first_day_of_month).count()

    total_expenses = ExpenseRecord.objects.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    pending_expenses = ExpenseRecord.objects.filter(status__in=[ExpenseRecord.Status.PENDING, ExpenseRecord.Status.SUBMITTED]).count()
    approved_expenses = ExpenseRecord.objects.filter(status=ExpenseRecord.Status.APPROVED).count()
    unpaid_expenses = ExpenseRecord.objects.filter(status__in=[ExpenseRecord.Status.UNPAID, ExpenseRecord.Status.APPROVED]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    month_expenses = ExpenseRecord.objects.filter(bill_date__gte=first_day_of_month).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    active_clients = Employee.objects.exclude(client_name="").values("client_name").distinct().count()
    unpaid_billing = BillingRecord.objects.filter(status__in=[BillingRecord.Status.SENT, BillingRecord.Status.OVERDUE]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    return JsonResponse({
        "total_employees": total_employees,
        "active_employees": active_employees,
        "inactive_employees": inactive_employees,
        "new_this_month": new_this_month,
        "total_expenses": float(total_expenses),
        "pending_expenses": pending_expenses,
        "approved_expenses": approved_expenses,
        "unpaid_expenses": float(unpaid_expenses),
        "month_expenses": float(month_expenses),
        "active_clients": active_clients,
        "unpaid_billing": float(unpaid_billing),
    })


# ==========================================
# EMPLOYEE MANAGEMENT VIEWS
# ==========================================

@login_required(login_url="login")
def employee_list_view(request):
    """Server-rendered Employee List with search, filtering, pagination and exports."""
    qs = Employee.objects.select_related("department", "designation", "supervisor").prefetch_related("documents").all()

    # Search
    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(employee_id__icontains=search)
            | Q(full_name__icontains=search)
            | Q(phone__icontains=search)
            | Q(email__icontains=search)
            | Q(client_name__icontains=search)
            | Q(passport_number__icontains=search)
            | Q(citizenship_number__icontains=search)
        )

    # Filters
    department_id = request.GET.get("department")
    if department_id:
        qs = qs.filter(department_id=department_id)

    designation_id = request.GET.get("designation")
    if designation_id:
        qs = qs.filter(designation_id=designation_id)

    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    employment_type = request.GET.get("employment_type")
    if employment_type:
        qs = qs.filter(employment_type=employment_type)

    # Exports
    export_format = request.GET.get("export")
    if export_format == "csv":
        log_action(request.user, AuditLog.Action.EXPORT, Employee(), f"Exported {qs.count()} employees to CSV", request)
        return export_employees_csv(qs)
    elif export_format == "excel":
        log_action(request.user, AuditLog.Action.EXPORT, Employee(), f"Exported {qs.count()} employees to Excel", request)
        return export_employees_excel(qs)
    elif export_format == "pdf":
        log_action(request.user, AuditLog.Action.EXPORT, Employee(), f"Exported {qs.count()} employees to PDF report", request)
        pdf_data = generate_employee_report_pdf(qs)
        response = HttpResponse(pdf_data, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="employee_directory.pdf"'
        return response

    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    departments = Department.objects.all()
    designations = Designation.objects.all()

    return render(request, "employees/employee_list.html", {
        "page_obj": page_obj,
        "employees": page_obj.object_list,
        "departments": departments,
        "designations": designations,
        "status_choices": Employee.Status.choices,
        "employment_type_choices": Employee.EmploymentType.choices,
        "total_count": qs.count(),
        "search": search,
        "current_department": department_id,
        "current_designation": designation_id,
        "current_status": status,
        "current_employment_type": employment_type,
    })


@login_required(login_url="login")
def employee_detail_view(request, pk):
    """Comprehensive Employee Profile Page."""
    employee = get_object_or_404(
        Employee.objects.select_related("department", "designation", "supervisor", "created_by")
        .prefetch_related("documents", "joinings", "expenses", "billing_records"),
        pk=pk,
    )
    documents = employee.documents.all()
    joinings = employee.joinings.all()
    expenses = employee.expenses.select_related("category_ref").all()
    audit_logs = AuditLog.objects.filter(model_name="Employee", object_id=str(employee.pk))[:15]

    return render(request, "employees/employee_detail.html", {
        "employee": employee,
        "documents": documents,
        "joinings": joinings,
        "expenses": expenses,
        "audit_logs": audit_logs,
    })


@login_required(login_url="login")
@hr_or_admin_required
def employee_create_view(request):
    """Create new Employee record."""
    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.created_by = request.user
            employee.save()
            log_action(request.user, AuditLog.Action.CREATE, employee, "Created employee record", request)
            messages.success(request, f"Employee '{employee.full_name}' ({employee.employee_id}) created successfully.")
            return redirect("employee-detail", pk=employee.pk)
    else:
        form = EmployeeForm()

    return render(request, "employees/employee_form.html", {
        "form": form,
        "title": "Create Employee",
        "action": "Create",
    })


@login_required(login_url="login")
@hr_or_admin_required
def employee_update_view(request, pk):
    """Edit Employee record."""
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            employee = form.save()
            log_action(request.user, AuditLog.Action.UPDATE, employee, "Updated employee details", request)
            messages.success(request, f"Employee '{employee.full_name}' updated successfully.")
            return redirect("employee-detail", pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)

    return render(request, "employees/employee_form.html", {
        "form": form,
        "employee": employee,
        "title": f"Edit {employee.full_name}",
        "action": "Update",
    })


@login_required(login_url="login")
@hr_or_admin_required
@require_POST
def employee_delete_view(request, pk):
    """Delete/Archive Employee."""
    employee = get_object_or_404(Employee, pk=pk)
    if employee.joinings.exists():
        messages.error(request, "Cannot delete employee with active joining records. Change status to Inactive instead.")
        return redirect("employee-detail", pk=employee.pk)

    name = employee.full_name
    emp_id = employee.employee_id
    log_action(request.user, AuditLog.Action.DELETE, employee, f"Deleted employee {name} ({emp_id})", request)
    employee.delete()
    messages.success(request, f"Employee '{name}' ({emp_id}) was deleted.")
    return redirect("employee-list")


@login_required(login_url="login")
def employee_print_view(request, pk):
    """Dedicated official A4 print template for Employee Record."""
    employee = get_object_or_404(
        Employee.objects.select_related("department", "designation", "supervisor"),
        pk=pk,
    )
    log_action(request.user, AuditLog.Action.PRINT, employee, "Printed employee profile", request)
    return render(request, "employees/employee_print.html", {
        "employee": employee,
        "print_date": timezone.now().date(),
    })


@login_required(login_url="login")
def employee_pdf_view(request, pk):
    """Generate and stream official Employee PDF."""
    employee = get_object_or_404(
        Employee.objects.select_related("department", "designation", "supervisor"),
        pk=pk,
    )
    log_action(request.user, AuditLog.Action.EXPORT, employee, "Generated employee profile PDF", request)
    pdf_bytes = generate_employee_pdf(employee)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="employee_{employee.employee_id}.pdf"'
    return response


# ==========================================
# JOINING FORM VIEWS
# ==========================================

@login_required(login_url="login")
def joining_print_view(request, pk):
    """Dedicated official A4 print template for Dubai Hiring / Joining Form."""
    joining = get_object_or_404(
        HiringRecord.objects.select_related("employee"),
        pk=pk,
    )
    log_action(request.user, AuditLog.Action.PRINT, joining, "Printed Dubai joining form", request)
    return render(request, "employees/joining_print.html", {
        "joining": joining,
        "employee": joining.employee,
    })


@login_required(login_url="login")
def joining_pdf_view(request, pk):
    """Generate official Dubai Joining Form PDF."""
    joining = get_object_or_404(
        HiringRecord.objects.select_related("employee"),
        pk=pk,
    )
    log_action(request.user, AuditLog.Action.EXPORT, joining, "Generated Dubai joining form PDF", request)
    pdf_bytes = generate_joining_pdf(joining)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="joining_form_{joining.pk}.pdf"'
    return response


@login_required(login_url="login")
def joining_photo(request, pk):
    """Stream passport photo for joining record."""
    joining = get_object_or_404(HiringRecord, pk=pk)
    try:
        file_handle = joining.passport_photo.open("rb")
    except (FileNotFoundError, ValueError) as error:
        raise Http404("Passport photo not found.") from error
    content_type = mimetypes.guess_type(joining.passport_photo.name)[0] or "application/octet-stream"
    return FileResponse(file_handle, content_type=content_type)


# ==========================================
# EXPENSE MANAGEMENT VIEWS
# ==========================================

@login_required(login_url="login")
def expense_list_view(request):
    """Server-rendered Expense Register with search, filtering, summary totals, and exports."""
    qs = ExpenseRecord.objects.select_related("employee", "department", "category_ref", "created_by", "approved_by").prefetch_related("items__product").all()

    # Search
    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(reference_number__icontains=search)
            | Q(vendor_name__icontains=search)
            | Q(description__icontains=search)
            | Q(invoice_number__icontains=search)
            | Q(employee__full_name__icontains=search)
            | Q(category__icontains=search)
        )

    # Date Range
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if start_date:
        qs = qs.filter(bill_date__gte=start_date)
    if end_date:
        qs = qs.filter(bill_date__lte=end_date)

    # Filters
    employee_id = request.GET.get("employee")
    if employee_id:
        qs = qs.filter(employee_id=employee_id)

    department_id = request.GET.get("department")
    if department_id:
        qs = qs.filter(department_id=department_id)

    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_ref_id=category_id)

    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    payment_method = request.GET.get("payment_method")
    if payment_method:
        qs = qs.filter(payment_method=payment_method)

    # Summary calculations
    total_amount = qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    pending_total = qs.filter(status__in=[ExpenseRecord.Status.PENDING, ExpenseRecord.Status.SUBMITTED]).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    approved_total = qs.filter(status=ExpenseRecord.Status.APPROVED).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    paid_total = qs.filter(status=ExpenseRecord.Status.PAID).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
    rejected_total = qs.filter(status=ExpenseRecord.Status.REJECTED).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Exports
    export_format = request.GET.get("export")
    if export_format == "csv":
        log_action(request.user, AuditLog.Action.EXPORT, ExpenseRecord(), f"Exported {qs.count()} expenses to CSV", request)
        return export_expenses_csv(qs)
    elif export_format == "excel":
        log_action(request.user, AuditLog.Action.EXPORT, ExpenseRecord(), f"Exported {qs.count()} expenses to Excel", request)
        return export_expenses_excel(qs)
    elif export_format == "pdf":
        log_action(request.user, AuditLog.Action.EXPORT, ExpenseRecord(), f"Exported {qs.count()} expenses to PDF report", request)
        date_str = f"{start_date} to {end_date}" if start_date and end_date else "All Dates"
        pdf_bytes = generate_expense_report_pdf(qs, date_range=date_str)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="expense_report.pdf"'
        return response

    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    employees = Employee.objects.all()
    departments = Department.objects.all()
    categories = ExpenseCategory.objects.all()

    return render(request, "expenses/expense_list.html", {
        "page_obj": page_obj,
        "expenses": page_obj.object_list,
        "employees": employees,
        "departments": departments,
        "categories": categories,
        "status_choices": ExpenseRecord.Status.choices,
        "payment_method_choices": ExpenseRecord.PaymentMethod.choices,
        "total_count": qs.count(),
        "total_amount": total_amount,
        "pending_total": pending_total,
        "approved_total": approved_total,
        "paid_total": paid_total,
        "rejected_total": rejected_total,
        "search": search,
        "start_date": start_date,
        "end_date": end_date,
        "current_employee": employee_id,
        "current_department": department_id,
        "current_category": category_id,
        "current_status": status,
        "current_payment_method": payment_method,
    })


@login_required(login_url="login")
def expense_detail_view(request, pk):
    """Expense detail page with line items, receipts and actions."""
    expense = get_object_or_404(
        ExpenseRecord.objects.select_related("employee", "department", "category_ref", "created_by", "approved_by")
        .prefetch_related("items__product"),
        pk=pk,
    )
    audit_logs = AuditLog.objects.filter(model_name="ExpenseRecord", object_id=str(expense.pk))[:10]

    return render(request, "expenses/expense_detail.html", {
        "expense": expense,
        "items": expense.items.all(),
        "audit_logs": audit_logs,
    })


@login_required(login_url="login")
def expense_create_view(request):
    """Create new Expense Record."""
    if request.method == "POST":
        form = ExpenseRecordForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            log_action(request.user, AuditLog.Action.CREATE, expense, f"Created expense {expense.amount} {expense.currency}", request)
            messages.success(request, f"Expense '{expense.reference_number}' created successfully.")
            return redirect("expense-detail", pk=expense.pk)
    else:
        form = ExpenseRecordForm(initial={"bill_date": timezone.now().date(), "currency": "AED"})

    return render(request, "expenses/expense_form.html", {
        "form": form,
        "title": "Create Expense Bill",
        "action": "Save Expense",
    })


@login_required(login_url="login")
def expense_update_view(request, pk):
    """Edit Expense Record."""
    expense = get_object_or_404(ExpenseRecord, pk=pk)
    if request.method == "POST":
        form = ExpenseRecordForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            expense = form.save()
            log_action(request.user, AuditLog.Action.UPDATE, expense, f"Updated expense details", request)
            messages.success(request, f"Expense '{expense.reference_number}' updated successfully.")
            return redirect("expense-detail", pk=expense.pk)
    else:
        form = ExpenseRecordForm(instance=expense)

    return render(request, "expenses/expense_form.html", {
        "form": form,
        "expense": expense,
        "title": f"Edit Expense {expense.reference_number}",
        "action": "Update Expense",
    })


@login_required(login_url="login")
@manager_or_above_required
@require_POST
def expense_approve_view(request, pk):
    """Approve an Expense."""
    expense = get_object_or_404(ExpenseRecord, pk=pk)
    expense.status = ExpenseRecord.Status.APPROVED
    expense.approved_by = request.user
    expense.approved_at = timezone.now()
    expense.save()
    log_action(request.user, AuditLog.Action.APPROVE, expense, f"Approved expense #{expense.reference_number}", request)
    messages.success(request, f"Expense '{expense.reference_number}' was approved.")
    return redirect("expense-detail", pk=expense.pk)


@login_required(login_url="login")
@manager_or_above_required
@require_POST
def expense_reject_view(request, pk):
    """Reject an Expense."""
    expense = get_object_or_404(ExpenseRecord, pk=pk)
    reason = request.POST.get("reason", "").strip()
    expense.status = ExpenseRecord.Status.REJECTED
    expense.rejection_reason = reason
    expense.save()
    log_action(request.user, AuditLog.Action.REJECT, expense, f"Rejected expense #{expense.reference_number}: {reason}", request)
    messages.warning(request, f"Expense '{expense.reference_number}' was rejected.")
    return redirect("expense-detail", pk=expense.pk)


@login_required(login_url="login")
@finance_or_admin_required
@require_POST
def expense_mark_paid_view(request, pk):
    """Mark an Expense as Paid."""
    expense = get_object_or_404(ExpenseRecord, pk=pk)
    expense.status = ExpenseRecord.Status.PAID
    expense.paid_date = timezone.now().date()
    expense.save()
    log_action(request.user, AuditLog.Action.MARK_PAID, expense, f"Marked expense #{expense.reference_number} as paid", request)
    messages.success(request, f"Expense '{expense.reference_number}' was marked as paid.")
    return redirect("expense-detail", pk=expense.pk)


@login_required(login_url="login")
@finance_or_admin_required
@require_POST
def expense_delete_view(request, pk):
    """Delete an Expense."""
    expense = get_object_or_404(ExpenseRecord, pk=pk)
    ref = expense.reference_number
    log_action(request.user, AuditLog.Action.DELETE, expense, f"Deleted expense {ref}", request)
    expense.delete()
    messages.success(request, f"Expense '{ref}' was deleted.")
    return redirect("expense-list")


@login_required(login_url="login")
def expense_print_view(request, pk):
    """Dedicated printable Payment Voucher template."""
    expense = get_object_or_404(
        ExpenseRecord.objects.select_related("employee", "department", "created_by", "approved_by")
        .prefetch_related("items__product"),
        pk=pk,
    )
    log_action(request.user, AuditLog.Action.PRINT, expense, "Printed expense voucher", request)
    return render(request, "expenses/expense_print.html", {
        "expense": expense,
        "items": expense.items.all(),
        "print_date": timezone.now().date(),
    })


@login_required(login_url="login")
def expense_pdf_view(request, pk):
    """Generate and stream official Expense Payment Voucher PDF."""
    expense = get_object_or_404(
        ExpenseRecord.objects.select_related("employee", "department", "created_by", "approved_by")
        .prefetch_related("items__product"),
        pk=pk,
    )
    log_action(request.user, AuditLog.Action.EXPORT, expense, "Generated expense payment voucher PDF", request)
    pdf_bytes = generate_expense_pdf(expense)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="voucher_{expense.reference_number}.pdf"'
    return response


@login_required(login_url="login")
def expense_receipt_download(request, pk):
    """Stream expense receipt file with permission checking."""
    expense = get_object_or_404(ExpenseRecord, pk=pk)
    if not expense.receipt_file:
        raise Http404("No receipt file attached.")
    try:
        file_handle = expense.receipt_file.open("rb")
    except FileNotFoundError as error:
        raise Http404("Receipt file not found on disk.") from error
    filename = expense.receipt_file.name.rsplit("/", 1)[-1]
    return FileResponse(file_handle, as_attachment=True, filename=filename)


# ==========================================
# DOCUMENT MANAGEMENT VIEWS
# ==========================================

@login_required(login_url="login")
def employee_document_download(request, pk):
    """Secure permission-checked download for employee documents."""
    document = get_object_or_404(EmployeeDocument, pk=pk)
    try:
        file_handle = document.file.open("rb")
    except FileNotFoundError as error:
        raise Http404("Document file not found.") from error
    filename = document.title or document.file.name.rsplit("/", 1)[-1]
    ext = Path(document.file.name).suffix
    if ext and not filename.lower().endswith(ext.lower()):
        filename = f"{filename}{ext}"
    return FileResponse(file_handle, as_attachment=True, filename=filename)


@login_required(login_url="login")
@require_POST
def employee_document_upload_view(request, employee_id):
    """Upload document for an employee."""
    employee = get_object_or_404(Employee, pk=employee_id)
    form = EmployeeDocumentForm(request.POST, request.FILES)
    if form.is_valid():
        doc = form.save(commit=False)
        doc.employee = employee
        doc.uploaded_by = request.user
        doc.save()
        log_action(request.user, AuditLog.Action.UPLOAD, doc, f"Uploaded document '{doc.title}' for {employee.full_name}", request)
        messages.success(request, f"Document '{doc.title}' uploaded successfully.")
    else:
        for error in form.errors.values():
            messages.error(request, error)
    return redirect("employee-detail", pk=employee.pk)


@login_required(login_url="login")
@hr_or_admin_required
@require_POST
def employee_document_delete_view(request, pk):
    """Delete an employee document."""
    document = get_object_or_404(EmployeeDocument, pk=pk)
    employee_pk = document.employee_id
    title = document.title
    log_action(request.user, AuditLog.Action.DELETE, document, f"Deleted document '{title}'", request)
    document.file.delete(save=False)
    document.delete()
    messages.success(request, f"Document '{title}' was deleted.")
    return redirect("employee-detail", pk=employee_pk)


# ==========================================
# REPORTS & ANALYTICS VIEWS
# ==========================================

@login_required(login_url="login")
def reports_home(request):
    """Reports navigation hub."""
    return render(request, "reports/reports_home.html")


@login_required(login_url="login")
def employee_reports_view(request):
    """Interactive Employee Reports with department/status breakdown."""
    dept_stats = (
        Department.objects.annotate(emp_count=Count("employees"))
        .filter(emp_count__gt=0)
        .order_by("-emp_count")
    )
    status_stats = (
        Employee.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    type_stats = (
        Employee.objects.values("employment_type")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    qs = Employee.objects.select_related("department", "designation").all()
    filter_status = request.GET.get("status")
    filter_dept = request.GET.get("department")
    if filter_status:
        qs = qs.filter(status=filter_status)
    if filter_dept:
        qs = qs.filter(department_id=filter_dept)

    # Exports
    export_format = request.GET.get("export")
    if export_format == "csv":
        return export_employees_csv(qs)
    elif export_format == "excel":
        return export_employees_excel(qs)
    elif export_format == "pdf":
        pdf_bytes = generate_employee_report_pdf(qs, title="Workforce Distribution Report")
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="workforce_report.pdf"'
        return response

    return render(request, "reports/employee_reports.html", {
        "dept_stats": dept_stats,
        "status_stats": status_stats,
        "type_stats": type_stats,
        "employees": qs[:50],
        "total_employees": Employee.objects.count(),
        "departments": Department.objects.all(),
        "status_choices": Employee.Status.choices,
    })


@login_required(login_url="login")
@finance_or_admin_required
def expense_reports_view(request):
    """Interactive Expense & Financial Analytics Reports."""
    qs = ExpenseRecord.objects.select_related("employee", "department", "category_ref").all()

    # Date filtering
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    if start_date:
        qs = qs.filter(bill_date__gte=start_date)
    if end_date:
        qs = qs.filter(bill_date__lte=end_date)

    # Category breakdown
    category_stats = (
        qs.values("category")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )

    # Status breakdown
    status_stats = (
        qs.values("status")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )

    # Department breakdown
    dept_stats = (
        qs.filter(department__isnull=False)
        .values("department__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )

    total_amount = qs.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    # Exports
    export_format = request.GET.get("export")
    if export_format == "csv":
        return export_expenses_csv(qs)
    elif export_format == "excel":
        return export_expenses_excel(qs)
    elif export_format == "pdf":
        date_str = f"{start_date} to {end_date}" if start_date and end_date else "All Records"
        pdf_bytes = generate_expense_report_pdf(qs, title="Financial Expense Analysis Report", date_range=date_str)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="financial_expense_report.pdf"'
        return response

    return render(request, "reports/expense_reports.html", {
        "category_stats": category_stats,
        "status_stats": status_stats,
        "dept_stats": dept_stats,
        "total_amount": total_amount,
        "total_count": qs.count(),
        "expenses": qs[:50],
        "start_date": start_date,
        "end_date": end_date,
    })


# ==========================================
# AUDIT LOG VIEWS
# ==========================================

@login_required(login_url="login")
@role_required([UserProfile.Role.ADMIN])
def audit_logs_view(request):
    """Audit trail inspection page."""
    qs = AuditLog.objects.select_related("user").all()

    action = request.GET.get("action")
    if action:
        qs = qs.filter(action=action)

    model_name = request.GET.get("model")
    if model_name:
        qs = qs.filter(model_name=model_name)

    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(object_repr__icontains=search)
            | Q(object_id__icontains=search)
            | Q(changes__icontains=search)
            | Q(user__username__icontains=search)
        )

    paginator = Paginator(qs, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "audit_logs.html", {
        "page_obj": page_obj,
        "audit_logs": page_obj.object_list,
        "action_choices": AuditLog.Action.choices,
        "current_action": action,
        "current_model": model_name,
        "search": search,
    })


# ==========================================
# REST FRAMEWORK VIEWSETS
# ==========================================

class SearchableModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def filter_search(self, queryset, fields):
        search = self.request.query_params.get("search", "").strip()
        if search:
            query = Q()
            for field in fields:
                query |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(query)
        status_val = self.request.query_params.get("status")
        if status_val:
            queryset = queryset.filter(status=status_val)
        return queryset


class DepartmentViewSet(SearchableModelViewSet):
    serializer_class = DepartmentSerializer
    queryset = Department.objects.all()

    def get_queryset(self):
        return self.filter_search(super().get_queryset(), ["name", "code"])


class DesignationViewSet(SearchableModelViewSet):
    serializer_class = DesignationSerializer
    queryset = Designation.objects.select_related("department").all()

    def get_queryset(self):
        return self.filter_search(super().get_queryset(), ["name", "department__name"])


class EmployeeViewSet(SearchableModelViewSet):
    serializer_class = EmployeeSerializer
    queryset = (
        Employee.objects.select_related("department", "designation", "supervisor")
        .prefetch_related("documents")
        .all()
    )
    permission_classes = [CanManageEmployees]

    def get_queryset(self):
        return self.filter_search(
            super().get_queryset(),
            ["employee_id", "full_name", "phone", "email", "client_name", "passport_number", "citizenship_number"],
        )

    def perform_create(self, serializer):
        emp = serializer.save(created_by=self.request.user)
        log_action(self.request.user, AuditLog.Action.CREATE, emp, "Created employee via API", self.request)

    def perform_update(self, serializer):
        emp = serializer.save()
        log_action(self.request.user, AuditLog.Action.UPDATE, emp, "Updated employee via API", self.request)

    def perform_destroy(self, instance):
        if instance.joinings.exists():
            raise ValidationError("Employees with joining records cannot be deleted.")
        for document in instance.documents.all():
            document.file.delete(save=False)
        log_action(self.request.user, AuditLog.Action.DELETE, instance, f"Deleted employee {instance.full_name}", self.request)
        instance.delete()


class HiringRecordViewSet(SearchableModelViewSet):
    serializer_class = HiringRecordSerializer
    queryset = HiringRecord.objects.select_related("employee").all()
    permission_classes = [CanManageEmployees]

    def get_queryset(self):
        return self.filter_search(
            super().get_queryset(),
            ["employee__employee_id", "employee__full_name", "client_name", "hiring_person_name", "mobile_number"],
        )

    def perform_create(self, serializer):
        joining = serializer.save(created_by=self.request.user)
        log_action(self.request.user, AuditLog.Action.CREATE, joining, f"Created joining record for {joining.employee.full_name}", self.request)

    def perform_destroy(self, instance):
        if instance.passport_photo:
            instance.passport_photo.delete(save=False)
        log_action(self.request.user, AuditLog.Action.DELETE, instance, "Deleted joining record", self.request)
        instance.delete()


class EmployeeDocumentViewSet(SearchableModelViewSet):
    serializer_class = EmployeeDocumentSerializer
    queryset = EmployeeDocument.objects.select_related("employee").all()
    permission_classes = [CanManageEmployees]

    def perform_create(self, serializer):
        doc = serializer.save(uploaded_by=self.request.user)
        log_action(self.request.user, AuditLog.Action.UPLOAD, doc, f"Uploaded document '{doc.title}'", self.request)

    def perform_destroy(self, instance):
        log_action(self.request.user, AuditLog.Action.DELETE, instance, f"Deleted document '{instance.title}'", self.request)
        instance.file.delete(save=False)
        instance.delete()


class BillingRecordViewSet(SearchableModelViewSet):
    serializer_class = BillingRecordSerializer
    queryset = BillingRecord.objects.select_related("employee").all()

    def get_queryset(self):
        return self.filter_search(
            super().get_queryset(),
            ["invoice_number", "client_name", "description"],
        )

    def perform_create(self, serializer):
        billing = serializer.save(created_by=self.request.user)
        log_action(self.request.user, AuditLog.Action.CREATE, billing, f"Created invoice {billing.invoice_number}", self.request)


class ExpenseRecordViewSet(SearchableModelViewSet):
    serializer_class = ExpenseRecordSerializer
    queryset = (
        ExpenseRecord.objects.select_related("employee", "department", "category_ref", "created_by", "approved_by")
        .prefetch_related("items__product")
        .all()
    )
    permission_classes = [CanManageExpenses]

    def get_queryset(self):
        return self.filter_search(
            super().get_queryset(),
            ["reference_number", "vendor_name", "category", "description", "invoice_number"],
        )

    def perform_create(self, serializer):
        expense = serializer.save(created_by=self.request.user)
        log_action(self.request.user, AuditLog.Action.CREATE, expense, f"Created expense {expense.reference_number}", self.request)

    def perform_update(self, serializer):
        expense = serializer.save()
        log_action(self.request.user, AuditLog.Action.UPDATE, expense, f"Updated expense {expense.reference_number}", self.request)

    def perform_destroy(self, instance):
        log_action(self.request.user, AuditLog.Action.DELETE, instance, f"Deleted expense {instance.reference_number}", self.request)
        instance.delete()

    @action(detail=True, methods=["post"], permission_classes=[CanApproveExpenses])
    def approve(self, request, pk=None):
        expense = self.get_object()
        expense.status = ExpenseRecord.Status.APPROVED
        expense.approved_by = request.user
        expense.approved_at = timezone.now()
        expense.save()
        log_action(request.user, AuditLog.Action.APPROVE, expense, f"Approved expense #{expense.reference_number}", request)
        return Response({"status": "approved"})

    @action(detail=True, methods=["post"], permission_classes=[CanApproveExpenses])
    def reject(self, request, pk=None):
        expense = self.get_object()
        reason = request.data.get("reason", "")
        expense.status = ExpenseRecord.Status.REJECTED
        expense.rejection_reason = reason
        expense.save()
        log_action(request.user, AuditLog.Action.REJECT, expense, f"Rejected expense #{expense.reference_number}: {reason}", request)
        return Response({"status": "rejected"})

    @action(detail=True, methods=["post"], permission_classes=[CanApproveExpenses])
    def mark_paid(self, request, pk=None):
        expense = self.get_object()
        expense.status = ExpenseRecord.Status.PAID
        expense.paid_date = timezone.now().date()
        expense.save()
        log_action(request.user, AuditLog.Action.MARK_PAID, expense, f"Marked expense #{expense.reference_number} as paid", request)
        return Response({"status": "paid"})


class ExpenseCategoryViewSet(SearchableModelViewSet):
    serializer_class = ExpenseCategorySerializer
    queryset = ExpenseCategory.objects.all()

    def get_queryset(self):
        return self.filter_search(super().get_queryset(), ["name"])


class ExpenseProductViewSet(SearchableModelViewSet):
    serializer_class = ExpenseProductSerializer
    queryset = ExpenseProduct.objects.select_related("category").all()

    def get_queryset(self):
        return self.filter_search(super().get_queryset(), ["name", "category__name"])


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related("user").all()
    permission_classes = [permissions.IsAdminUser]


# ==========================================
# CUSTOM ERROR HANDLERS
# ==========================================

def custom_bad_request(request, exception=None):
    return render(request, "errors/400.html", status=400)


def custom_permission_denied(request, exception=None):
    return render(request, "errors/403.html", status=403)


def custom_page_not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def custom_server_error(request):
    return render(request, "errors/500.html", status=500)