from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("departments", views.DepartmentViewSet)
router.register("designations", views.DesignationViewSet)
router.register("employees", views.EmployeeViewSet)
router.register("joinings", views.HiringRecordViewSet)
router.register("documents", views.EmployeeDocumentViewSet)
router.register("billing", views.BillingRecordViewSet)
router.register("expenses", views.ExpenseRecordViewSet)
router.register("expense-categories", views.ExpenseCategoryViewSet)
router.register("expense-products", views.ExpenseProductViewSet)
router.register("audit-logs", views.AuditLogViewSet)

urlpatterns = [
    # Auth & Workspace
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login-page"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.home, name="home"),
    path("api/dashboard-stats/", views.dashboard_stats_api, name="dashboard-stats-api"),

    # Employees
    path("employees/", views.employee_list_view, name="employee-list"),
    path("employees/new/", views.employee_create_view, name="employee-create"),
    path("employees/<int:pk>/", views.employee_detail_view, name="employee-detail"),
    path("employees/<int:pk>/edit/", views.employee_update_view, name="employee-edit"),
    path("employees/<int:pk>/delete/", views.employee_delete_view, name="employee-delete"),
    path("employees/<int:pk>/print/", views.employee_print_view, name="employee-print"),
    path("employees/<int:pk>/pdf/", views.employee_pdf_view, name="employee-pdf"),
    path("employees/<int:employee_id>/upload-document/", views.employee_document_upload_view, name="employee-document-upload"),

    # Dubai Hiring & Joining Forms
    path("joinings/<int:pk>/print/", views.joining_print_view, name="joining-print"),
    path("joinings/<int:pk>/pdf/", views.joining_pdf_view, name="joining-pdf"),
    path("joinings/<int:pk>/photo/", views.joining_photo, name="joining-photo"),

    # Expenses
    path("expenses/", views.expense_list_view, name="expense-list"),
    path("expenses/new/", views.expense_create_view, name="expense-create"),
    path("expenses/<int:pk>/", views.expense_detail_view, name="expense-detail"),
    path("expenses/<int:pk>/edit/", views.expense_update_view, name="expense-edit"),
    path("expenses/<int:pk>/delete/", views.expense_delete_view, name="expense-delete"),
    path("expenses/<int:pk>/approve/", views.expense_approve_view, name="expense-approve"),
    path("expenses/<int:pk>/reject/", views.expense_reject_view, name="expense-reject"),
    path("expenses/<int:pk>/mark-paid/", views.expense_mark_paid_view, name="expense-mark-paid"),
    path("expenses/<int:pk>/print/", views.expense_print_view, name="expense-print"),
    path("expenses/<int:pk>/pdf/", views.expense_pdf_view, name="expense-pdf"),
    path("expenses/<int:pk>/receipt/", views.expense_receipt_download, name="expense-receipt-download"),

    # Documents
    path("documents/<int:pk>/download/", views.employee_document_download, name="employee-document-download"),
    path("documents/<int:pk>/delete/", views.employee_document_delete_view, name="employee-document-delete"),

    # Reports
    path("reports/", views.reports_home, name="reports-home"),
    path("reports/employees/", views.employee_reports_view, name="reports-employees"),
    path("reports/expenses/", views.expense_reports_view, name="reports-expenses"),

    # Audit Logs
    path("audit-logs/", views.audit_logs_view, name="audit-logs"),

    # REST API
    path("api/", include((router.urls, "api"), namespace="api")),
]