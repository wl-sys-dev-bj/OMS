import io
from decimal import Decimal
from tempfile import TemporaryDirectory
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

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


class EmployeeWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(username="admin", password="admin-password", email="admin@test.com")
        UserProfile.objects.update_or_create(user=self.admin_user, defaults={"role": UserProfile.Role.ADMIN})

        self.hr_user = User.objects.create_user(username="hr_staff", password="hr-password", email="hr@test.com")
        UserProfile.objects.update_or_create(user=self.hr_user, defaults={"role": UserProfile.Role.HR})

        self.emp_user = User.objects.create_user(username="standard_emp", password="emp-password", email="emp@test.com")
        UserProfile.objects.update_or_create(user=self.emp_user, defaults={"role": UserProfile.Role.EMPLOYEE})

        self.dept = Department.objects.create(name="Operations", code="OPS")
        self.desig = Designation.objects.create(name="Coordinator", department=self.dept)

        self.client = APIClient()
        self.client.force_login(self.admin_user)

    def test_create_and_view_employee(self):
        response = self.client.post(reverse("employee-create"), {
            "employee_id": "EMP-901",
            "first_name": "Nima",
            "last_name": "Sherpa",
            "full_name": "Nima Sherpa",
            "phone": "+971 50 000 1111",
            "email": "nima@test.com",
            "department": self.dept.pk,
            "designation": self.desig.pk,
            "employment_type": "full_time",
            "salary": "3500.00",
            "status": "active",
            "nationality": "Nepali",
        })
        self.assertEqual(response.status_code, 302)
        emp = Employee.objects.get(employee_id="EMP-901")
        self.assertEqual(emp.full_name, "Nima Sherpa")
        self.assertEqual(emp.salary, Decimal("3500.00"))

        detail_response = self.client.get(reverse("employee-detail", args=[emp.pk]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Nima Sherpa")
        self.assertContains(detail_response, "EMP-901")

    def test_employee_id_uniqueness_validation(self):
        Employee.objects.create(employee_id="EMP-DUP-1", full_name="User One", phone="12345")
        response = self.client.post(reverse("employee-create"), {
            "employee_id": "EMP-DUP-1",
            "full_name": "User Two",
            "phone": "67890",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already assigned")

    def test_search_and_filter_employees(self):
        Employee.objects.create(employee_id="EMP-SRCH-1", full_name="Aarav Sharma", phone="9801111111", department=self.dept, status=Employee.Status.ACTIVE)
        Employee.objects.create(employee_id="EMP-SRCH-2", full_name="Bina Gurung", phone="9802222222", status=Employee.Status.ON_LEAVE)

        search_res = self.client.get(reverse("employee-list") + "?search=Aarav")
        self.assertEqual(search_res.status_code, 200)
        self.assertContains(search_res, "Aarav Sharma")
        self.assertNotContains(search_res, "Bina Gurung")

        filter_res = self.client.get(reverse("employee-list") + "?status=on_leave")
        self.assertEqual(filter_res.status_code, 200)
        self.assertContains(filter_res, "Bina Gurung")
        self.assertNotContains(filter_res, "Aarav Sharma")

    def test_employee_print_and_pdf_generation(self):
        emp = Employee.objects.create(employee_id="EMP-PRN-1", full_name="Print Test User", phone="9800000000", salary=Decimal("2500.00"), department=self.dept)
        
        print_res = self.client.get(reverse("employee-print", args=[emp.pk]))
        self.assertEqual(print_res.status_code, 200)
        self.assertContains(print_res, "Print Test User")
        self.assertContains(print_res, "EMP-PRN-1")

        pdf_res = self.client.get(reverse("employee-pdf", args=[emp.pk]))
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res["Content-Type"], "application/pdf")
        self.assertTrue(len(pdf_res.content) > 500)


class ExpenseWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(username="admin_exp", password="password123")
        UserProfile.objects.update_or_create(user=self.admin_user, defaults={"role": UserProfile.Role.ADMIN})

        self.finance_user = User.objects.create_user(username="finance_staff", password="password123")
        UserProfile.objects.update_or_create(user=self.finance_user, defaults={"role": UserProfile.Role.FINANCE})

        self.manager_user = User.objects.create_user(username="manager_staff", password="password123")
        UserProfile.objects.update_or_create(user=self.manager_user, defaults={"role": UserProfile.Role.MANAGER})

        self.emp = Employee.objects.create(employee_id="EMP-EXP-1", full_name="Expense User", phone="12345")
        self.category = ExpenseCategory.objects.create(name="Office Logistics")

        self.client = APIClient()
        self.client.force_login(self.admin_user)

    def test_create_expense_with_receipt_and_approve(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            receipt = SimpleUploadedFile("receipt.pdf", b"%PDF-1.4 test receipt content", content_type="application/pdf")
            response = self.client.post(reverse("expense-create"), {
                "reference_number": "EXP-TST-001",
                "employee": self.emp.pk,
                "category_ref": self.category.pk,
                "vendor_name": "Gulf Supplies",
                "description": "Office paper and pens",
                "amount": "450.00",
                "currency": "AED",
                "bill_date": str(date.today()),
                "status": "pending",
                "payment_method": "cash",
                "receipt_file": receipt,
            })
            self.assertEqual(response.status_code, 302)
            expense = ExpenseRecord.objects.get(reference_number="EXP-TST-001")
            self.assertEqual(expense.amount, Decimal("450.00"))
            self.assertEqual(expense.status, ExpenseRecord.Status.PENDING)
            self.assertTrue(bool(expense.receipt_file))

            # Approve
            approve_res = self.client.post(reverse("expense-approve", args=[expense.pk]))
            self.assertEqual(approve_res.status_code, 302)
            expense.refresh_from_db()
            self.assertEqual(expense.status, ExpenseRecord.Status.APPROVED)
            self.assertEqual(expense.approved_by, self.admin_user)

            # Mark Paid
            paid_res = self.client.post(reverse("expense-mark-paid", args=[expense.pk]))
            self.assertEqual(paid_res.status_code, 302)
            expense.refresh_from_db()
            self.assertEqual(expense.status, ExpenseRecord.Status.PAID)
            self.assertEqual(expense.paid_date, date.today())

    def test_expense_pdf_and_print_generation(self):
        exp = ExpenseRecord.objects.create(
            reference_number="EXP-PDF-1",
            employee=self.emp,
            vendor_name="Dubai Tech Store",
            amount=Decimal("1200.00"),
            currency="AED",
            bill_date=date.today(),
            status=ExpenseRecord.Status.APPROVED,
        )
        print_res = self.client.get(reverse("expense-print", args=[exp.pk]))
        self.assertEqual(print_res.status_code, 200)
        self.assertContains(print_res, "EXP-PDF-1")
        self.assertContains(print_res, "1200.00")

        pdf_res = self.client.get(reverse("expense-pdf", args=[exp.pk]))
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res["Content-Type"], "application/pdf")
        self.assertTrue(len(pdf_res.content) > 500)


class DocumentAndSecurityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="admin_sec", password="password")
        UserProfile.objects.update_or_create(user=self.admin, defaults={"role": UserProfile.Role.ADMIN})

        self.unauth_user = User.objects.create_user(username="standard_user", password="password")
        UserProfile.objects.update_or_create(user=self.unauth_user, defaults={"role": UserProfile.Role.EMPLOYEE})

        self.emp = Employee.objects.create(employee_id="EMP-SEC-1", full_name="Protected User", phone="12345")

    def test_anonymous_access_redirects_to_login(self):
        client = APIClient()
        response = client.get(reverse("employee-list"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")) or response.url.startswith("/login"))

    def test_document_upload_and_download_security(self):
        client = APIClient()
        client.force_login(self.admin)

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            doc_file = SimpleUploadedFile("contract.pdf", b"%PDF-1.4 sample contract", content_type="application/pdf")
            response = client.post(reverse("employee-document-upload", args=[self.emp.pk]), {
                "title": "Employment Contract 2026",
                "category": "contract",
                "file": doc_file,
            })
            self.assertEqual(response.status_code, 302)
            doc = EmployeeDocument.objects.get(employee=self.emp, title="Employment Contract 2026")

            # Authenticated user can download
            dl_res = client.get(reverse("employee-document-download", args=[doc.pk]))
            self.assertEqual(dl_res.status_code, 200)
            self.assertEqual(dl_res["Content-Type"], "application/pdf")
            dl_res.close()

            # Anonymous cannot download
            anon_client = APIClient()
            anon_res = anon_client.get(reverse("employee-document-download", args=[doc.pk]))
            self.assertEqual(anon_res.status_code, 302)
            anon_res.close()


class ReportingAndExportsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username="admin_rep", password="password")
        UserProfile.objects.update_or_create(user=self.admin, defaults={"role": UserProfile.Role.ADMIN})

        self.client = APIClient()
        self.client.force_login(self.admin)

        self.dept = Department.objects.create(name="Fleet Logistics")
        self.emp1 = Employee.objects.create(employee_id="EMP-R1", full_name="Alpha User", phone="111", department=self.dept, status=Employee.Status.ACTIVE)
        self.emp2 = Employee.objects.create(employee_id="EMP-R2", full_name="Beta User", phone="222", department=self.dept, status=Employee.Status.ON_LEAVE)

        ExpenseRecord.objects.create(reference_number="EXP-R1", vendor_name="Fuel Co", amount=Decimal("600.00"), currency="AED", bill_date=date.today(), status=ExpenseRecord.Status.PAID)
        ExpenseRecord.objects.create(reference_number="EXP-R2", vendor_name="Tire Co", amount=Decimal("400.00"), currency="AED", bill_date=date.today(), status=ExpenseRecord.Status.APPROVED)

    def test_employee_reports_page_and_exports(self):
        response = self.client.get(reverse("reports-employees"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fleet Logistics")

        # Excel export
        excel_res = self.client.get(reverse("reports-employees") + "?export=excel")
        self.assertEqual(excel_res.status_code, 200)
        self.assertEqual(excel_res["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # CSV export
        csv_res = self.client.get(reverse("reports-employees") + "?export=csv")
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res["Content-Type"], "text/csv; charset=utf-8")
        self.assertContains(csv_res, "Alpha User")

        # PDF export
        pdf_res = self.client.get(reverse("reports-employees") + "?export=pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res["Content-Type"], "application/pdf")

    def test_expense_reports_page_and_exports(self):
        response = self.client.get(reverse("reports-expenses"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "1000.00")

        # Excel export
        excel_res = self.client.get(reverse("reports-expenses") + "?export=excel")
        self.assertEqual(excel_res.status_code, 200)

        # CSV export
        csv_res = self.client.get(reverse("reports-expenses") + "?export=csv")
        self.assertEqual(csv_res.status_code, 200)
        self.assertContains(csv_res, "EXP-R1")
        self.assertContains(csv_res, "Fuel Co")

        # PDF export
        pdf_res = self.client.get(reverse("reports-expenses") + "?export=pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res["Content-Type"], "application/pdf")


class DashboardAndLegacyApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(username="manager", password="test-password")
        UserProfile.objects.update_or_create(user=self.user, defaults={"role": UserProfile.Role.ADMIN})

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.force_login(self.user)

    def test_dashboard_renders_with_overlays_and_slots(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="employee-detail-overlay"')
        self.assertContains(response, 'id="employee-print-sheet-slot"')
        self.assertContains(response, 'id="joining-print-sheet"')
        self.assertContains(response, 'id="billing-form"')
        self.assertContains(response, 'id="expense-form"')
        self.assertContains(response, 'name="citizenship_number"')

    def test_dashboard_stats_api_returns_aggregates(self):
        response = self.client.get(reverse("dashboard-stats-api"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_employees", data)
        self.assertIn("total_expenses", data)
        self.assertIn("active_employees", data)

    def test_joining_creation_and_photo(self):
        emp = Employee.objects.create(employee_id="EMP-LEG-1", full_name="Legacy User", phone="9800000000")
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            res = self.client.post("/api/joinings/", {
                "employee": emp.pk,
                "client_name": "Cedar Logistics",
                "hiring_person_name": "Mina Shrestha",
                "joining_date": "2026-11-15",
                "nationality": "Nepali",
                "passport_photo": SimpleUploadedFile("photo.png", b"\x89PNG\r\n\x1a\nphoto", content_type="image/png"),
            }, format="multipart")
            self.assertEqual(res.status_code, 201)
            joining_id = res.data["id"]

            photo_res = self.client.get(reverse("joining-photo", args=[joining_id]))
            self.assertEqual(photo_res.status_code, 200)
            self.assertEqual(photo_res["Content-Type"], "image/png")
            photo_res.close()
