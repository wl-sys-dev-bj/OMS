from django.test import TestCase
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Employee, EmployeeDocument, ExpenseRecord, HiringRecord


class ManagementApiTests(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(username="manager", password="test-password")
		self.client = APIClient()
		self.client.force_authenticate(user=self.user)
		self.client.force_login(self.user)

	def test_api_requires_authentication(self):
		anonymous_client = APIClient()
		response = anonymous_client.get("/api/employees/")

		self.assertEqual(response.status_code, 403)

	def test_employee_and_joining_records_are_created_through_the_api(self):
		employee_response = self.client.post(
			"/api/employees/",
			{
				"employee_id": "EMP-104",
				"full_name": "Asha Rai",
				"phone": "+977 9800000000",
				"client_name": "Cedar Logistics",
			},
			format="json",
		)

		self.assertEqual(employee_response.status_code, 201)
		employee = Employee.objects.get(employee_id="EMP-104")
		joining_response = self.client.post(
			"/api/joinings/",
			{
				"employee": employee.pk,
				"client_name": "Cedar Logistics",
				"hiring_person_name": "Mina Shrestha",
				"hiring_person_employee_id": "HR-12",
				"joining_date": "2026-11-15",
				"destination": "Dubai, UAE",
			},
			format="json",
		)

		self.assertEqual(joining_response.status_code, 201)
		self.assertEqual(joining_response.data["employee_id"], "EMP-104")
		self.assertEqual(joining_response.data["hiring_person_employee_id"], "HR-12")

	def test_joining_application_fields_and_passport_photo_are_saved(self):
		employee = Employee.objects.create(
			employee_id="EMP-107",
			full_name="Sita Gurung",
			phone="9800000003",
		)
		with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			response = self.client.post(
				"/api/joinings/",
				{
					"employee": employee.pk,
					"client_name": "Cedar Logistics",
					"hiring_person_name": "Mina Shrestha",
					"application_date": "2026-10-01",
					"joining_date": "2026-11-15",
					"father_name": "Hari Gurung",
					"nationality": "Nepali",
					"city": "Pokhara",
					"visa_status": "Applied",
					"passport_number": "P1234567",
					"citizenship_number": "CIT123456",
					"mobile_number": "9800000003",
					"basic_salary": "1500.00",
					"commission_percent": "5.00",
					"allowance": "Transport",
					"room_provided": "true",
					"job_title": "Kitchen assistant",
					"hr_name": "Mina Shrestha",
					"passport_photo": SimpleUploadedFile(
						"portrait.png",
						b"\\x89PNG\\r\\n\\x1a\\nphoto",
						content_type="image/png",
					),
				},
				format="multipart",
			)

			self.assertEqual(response.status_code, 201)
			joining = HiringRecord.objects.get(pk=response.data["id"])
			self.assertEqual(joining.father_name, "Hari Gurung")
			self.assertEqual(joining.citizenship_number, "CIT123456")
			self.assertEqual(str(joining.basic_salary), "1500.00")
			self.assertTrue(joining.room_provided)
			self.assertTrue(response.data["passport_photo_url"])

			photo_response = self.client.get(response.data["passport_photo_url"])
			self.assertEqual(photo_response.status_code, 200)
			self.assertEqual(photo_response["Content-Type"], "image/png")
			self.assertEqual(b"".join(photo_response.streaming_content), b"\\x89PNG\\r\\n\\x1a\\nphoto")

			anonymous_client = APIClient()
			anonymous_response = anonymous_client.get(reverse("joining-photo", args=[joining.pk]))
			self.assertEqual(anonymous_response.status_code, 302)

	def test_joining_form_creates_employee_for_new_applicant(self):
		response = self.client.post(
			"/api/joinings/",
			{
				"employee": "",
				"applicant_name": "New Applicant",
				"client_name": "Cedar Logistics",
				"hiring_person_name": "Mina Shrestha",
				"joining_date": "2026-12-01",
				"mobile_number": "0500000000",
				"nationality": "Nepali",
				"job_title": "Kitchen assistant",
				"assigned_employee_number": "",
			},
			format="multipart",
		)

		self.assertEqual(response.status_code, 201)
		employee = Employee.objects.get(pk=response.data["employee"])
		self.assertEqual(employee.full_name, "New Applicant")
		self.assertTrue(employee.employee_id.startswith("JOIN-"))
		self.assertEqual(employee.phone, "0500000000")
		self.assertEqual(employee.created_by, self.user)

	def test_joining_can_save_without_company_tracking_fields(self):
		employee = Employee.objects.create(
			employee_id="EMP-108",
			full_name="Rita Shahi",
			phone="0500000001",
			client_name="Cedar Logistics",
		)
		response = self.client.post(
			"/api/joinings/",
			{
				"employee": employee.pk,
				"joining_date": "2026-12-20",
				"hr_name": "Mina Shrestha",
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(response.data["client_name"], "Cedar Logistics")
		self.assertEqual(response.data["hiring_person_name"], "Mina Shrestha")

	def test_expense_records_can_be_created_listed_and_deleted(self):
		category_response = self.client.post(
			"/api/expense-categories/",
			{"name": "Office supplies"},
			format="json",
		)
		self.assertEqual(category_response.status_code, 201)
		product_response = self.client.post(
			"/api/expense-products/",
			{
				"name": "Printer toner",
				"category": category_response.data["id"],
				"unit_price": "212.75",
				"currency": "AED",
			},
			format="json",
		)
		self.assertEqual(product_response.status_code, 201)

		response = self.client.post(
			"/api/expenses/",
			{
				"reference_number": "EXP-2026-014",
				"vendor_name": "Harbor Office Supplies",
				"category": "Office supplies",
				"bill_date": "2026-10-01",
				"due_date": "2026-10-15",
				"status": "unpaid",
				"notes": "October office order",
				"items": [{"product": product_response.data["id"], "quantity": "2.00"}],
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		expense = ExpenseRecord.objects.get(reference_number="EXP-2026-014")
		self.assertEqual(expense.created_by, self.user)
		self.assertEqual(expense.amount, 425.50)
		self.assertEqual(expense.description, "Printer toner")
		self.assertEqual(expense.items.count(), 1)

		update_response = self.client.patch(
			f"/api/expenses/{expense.pk}/",
			{
				"status": "paid",
				"paid_date": "2026-10-03",
				"items": [{"product": product_response.data["id"], "quantity": "3.00"}],
			},
			format="json",
		)
		self.assertEqual(update_response.status_code, 200)
		expense.refresh_from_db()
		self.assertEqual(expense.status, ExpenseRecord.Status.PAID)
		self.assertEqual(str(expense.paid_date), "2026-10-03")
		self.assertEqual(expense.amount, 638.25)

		list_response = self.client.get("/api/expenses/?search=Harbor")
		self.assertEqual(list_response.status_code, 200)
		self.assertEqual(len(list_response.data), 1)
		self.assertEqual(list_response.data[0]["status"], "paid")
		self.assertEqual(list_response.data[0]["vendor_name"], "Harbor Office Supplies")

		delete_response = self.client.delete(f"/api/expenses/{expense.pk}/")
		self.assertEqual(delete_response.status_code, 204)
		self.assertFalse(ExpenseRecord.objects.filter(pk=expense.pk).exists())

	def test_existing_expense_without_product_lines_can_still_be_updated(self):
		expense = ExpenseRecord.objects.create(
			reference_number="OLD-EXP-1",
			vendor_name="Existing supplier",
			category="Utilities",
			description="Legacy expense entry",
			amount="96.25",
			currency="AED",
			bill_date="2026-09-30",
			created_by=self.user,
		)

		response = self.client.patch(
			f"/api/expenses/{expense.pk}/",
			{"status": "paid", "paid_date": "2026-10-02"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		expense.refresh_from_db()
		self.assertEqual(expense.status, ExpenseRecord.Status.PAID)
		self.assertEqual(expense.amount, 96.25)

	def test_dashboard_keeps_invoice_and_pos_sections_separate(self):
		response = self.client.get("/dashboard/")

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'id="billing-form"')
		self.assertContains(response, 'id="expense-form"')
		self.assertNotContains(response, "Company tracking")
		self.assertContains(response, 'name="citizenship_number"')
		self.assertContains(response, 'list="nationality-options"')
		self.assertContains(response, 'id="employee-detail-overlay"')
		self.assertContains(response, 'id="employee-print-sheet-slot"')
		self.assertEqual(response.content.count(b'id="expenses-table"'), 1)
		self.assertEqual(response.content.count(b'id="expense-search"'), 1)

	def test_document_upload_rejects_unsupported_file_types(self):
		employee = Employee.objects.create(
			employee_id="EMP-105",
			full_name="Bina Thapa",
			phone="9800000001",
		)
		response = self.client.post(
			"/api/documents/",
			{
				"employee": employee.pk,
				"title": "Executable",
				"category": "other",
				"file": SimpleUploadedFile("payload.exe", b"not a document"),
			},
			format="multipart",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("file", response.data)

	def test_document_download_requires_login(self):
		anonymous_client = APIClient()
		response = anonymous_client.get(reverse("employee-document-download", args=[999]))

		self.assertEqual(response.status_code, 302)

	def test_document_download_returns_private_file_for_authenticated_user(self):
		employee = Employee.objects.create(
			employee_id="EMP-106",
			full_name="Nima Karki",
			phone="9800000002",
		)
		with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			document = EmployeeDocument.objects.create(
				employee=employee,
				title="Passport scan.pdf",
				category=EmployeeDocument.Category.PASSPORT,
				file=SimpleUploadedFile("passport.pdf", b"private document"),
				uploaded_by=self.user,
			)

			response = self.client.get(reverse("employee-document-download", args=[document.pk]))

			self.assertEqual(response.status_code, 200)
			self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
			self.assertEqual(b"".join(response.streaming_content), b"private document")
