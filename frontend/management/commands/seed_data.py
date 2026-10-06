from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from frontend.models import (
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


class Command(BaseCommand):
    help = "Seed database with realistic departments, roles, employees, expenses, and joinings."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding database with realistic sample data..."))
        User = get_user_model()

        # 1. Users & Roles
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={"email": "admin@oms.com", "first_name": "System", "last_name": "Administrator", "is_staff": True, "is_superuser": True}
        )
        admin_user.set_password("admin123")
        admin_user.save()
        UserProfile.objects.update_or_create(user=admin_user, defaults={"role": UserProfile.Role.ADMIN, "phone": "+971 50 111 0001"})

        hr_user, _ = User.objects.get_or_create(
            username="hr_user",
            defaults={"email": "hr@oms.com", "first_name": "Mina", "last_name": "Shrestha", "is_staff": True}
        )
        hr_user.set_password("hr123")
        hr_user.save()
        UserProfile.objects.update_or_create(user=hr_user, defaults={"role": UserProfile.Role.HR, "phone": "+971 50 222 0002"})

        finance_user, _ = User.objects.get_or_create(
            username="finance_user",
            defaults={"email": "finance@oms.com", "first_name": "Rashid", "last_name": "Al Mansoori", "is_staff": True}
        )
        finance_user.set_password("finance123")
        finance_user.save()
        UserProfile.objects.update_or_create(user=finance_user, defaults={"role": UserProfile.Role.FINANCE, "phone": "+971 50 333 0003"})

        manager_user, _ = User.objects.get_or_create(
            username="manager_user",
            defaults={"email": "manager@oms.com", "first_name": "David", "last_name": "Miller", "is_staff": True}
        )
        manager_user.set_password("manager123")
        manager_user.save()
        UserProfile.objects.update_or_create(user=manager_user, defaults={"role": UserProfile.Role.MANAGER, "phone": "+971 50 444 0004"})

        emp_user, _ = User.objects.get_or_create(
            username="employee_user",
            defaults={"email": "employee@oms.com", "first_name": "Asha", "last_name": "Rai", "is_staff": False}
        )
        emp_user.set_password("emp123")
        emp_user.save()
        UserProfile.objects.update_or_create(user=emp_user, defaults={"role": UserProfile.Role.EMPLOYEE, "phone": "+971 50 555 0005"})

        # 2. Departments
        depts_data = [
            ("Operations", "OPS", "Core field and workforce deployment operations."),
            ("Human Resources", "HR", "Talent acquisition, onboarding, visa processing, and employee care."),
            ("Finance & Accounts", "FIN", "Financial planning, expense management, billing, and reporting."),
            ("Logistics & Fleet", "LOG", "Fleet management, transport, and warehousing operations."),
            ("Hospitality Services", "HOSP", "Client catering and facility staff management."),
        ]
        dept_objs = {}
        for name, code, desc in depts_data:
            dept, _ = Department.objects.get_or_create(name=name, defaults={"code": code, "description": desc})
            dept_objs[name] = dept

        # 3. Designations
        desigs_data = [
            ("Operations Supervisor", dept_objs["Operations"]),
            ("Field Coordinator", dept_objs["Operations"]),
            ("Senior HR Specialist", dept_objs["Human Resources"]),
            ("Visa & PRO Officer", dept_objs["Human Resources"]),
            ("Accounts Officer", dept_objs["Finance & Accounts"]),
            ("Fleet Driver", dept_objs["Logistics & Fleet"]),
            ("Warehouse Associate", dept_objs["Logistics & Fleet"]),
            ("Kitchen Assistant", dept_objs["Hospitality Services"]),
            ("Barista", dept_objs["Hospitality Services"]),
        ]
        desig_objs = {}
        for name, dept in desigs_data:
            desig, _ = Designation.objects.get_or_create(name=name, defaults={"department": dept})
            desig_objs[name] = desig

        # 4. Expense Categories & Products
        cats_data = [
            ("Office Supplies", "Stationery, paper, toner, and office essentials."),
            ("Transportation & Fuel", "Local vehicle fuel, Salik toll, and taxi charges."),
            ("Visa & Immigration", "Government fees, medical tests, and visa processing."),
            ("Accommodation & Utilities", "Staff housing rent, DEWA utilities, and maintenance."),
            ("Meals & Catering", "Duty meals, hospitality expenses, and staff refreshments."),
            ("Equipment & Maintenance", "Tools, safety gear, uniform replacements, and repairs."),
        ]
        cat_objs = {}
        for name, desc in cats_data:
            cat, _ = ExpenseCategory.objects.get_or_create(name=name, defaults={"description": desc})
            cat_objs[name] = cat

        products_data = [
            ("Printer Paper Box (A4)", cat_objs["Office Supplies"], Decimal("120.00")),
            ("Black Toner Cartridge", cat_objs["Office Supplies"], Decimal("280.00")),
            ("Fuel Card Top-up", cat_objs["Transportation & Fuel"], Decimal("500.00")),
            ("Vehicle Maintenance & Service", cat_objs["Transportation & Fuel"], Decimal("450.00")),
            ("Emirates ID & Medical Fee", cat_objs["Visa & Immigration"], Decimal("850.00")),
            ("Visa Stamping Fee", cat_objs["Visa & Immigration"], Decimal("1200.00")),
            ("DEWA Electricity & Water", cat_objs["Accommodation & Utilities"], Decimal("650.00")),
            ("Staff House Cleaning Supplies", cat_objs["Accommodation & Utilities"], Decimal("150.00")),
            ("Duty Staff Lunch Pack (x10)", cat_objs["Meals & Catering"], Decimal("180.00")),
            ("Safety Shoes & Hi-Vis Vest", cat_objs["Equipment & Maintenance"], Decimal("110.00")),
        ]
        for name, cat, price in products_data:
            ExpenseProduct.objects.get_or_create(name=name, category=cat, defaults={"unit_price": price, "currency": "AED"})

        # 5. Employees (15+ realistic employees)
        employees_data = [
            {
                "employee_id": "EMP-1001", "first_name": "Asha", "last_name": "Rai", "full_name": "Asha Rai",
                "phone": "+971 50 123 4567", "email": "asha.rai@company.com", "nationality": "Nepali", "gender": "female",
                "dept": dept_objs["Hospitality Services"], "desig": desig_objs["Kitchen Assistant"],
                "salary": Decimal("1800.00"), "status": Employee.Status.ACTIVE, "client": "Cedar Logistics Dining",
                "joining_date": date(2025, 3, 1), "passport": "N12345678", "citizenship": "01-05-72-12345",
            },
            {
                "employee_id": "EMP-1002", "first_name": "Sita", "last_name": "Gurung", "full_name": "Sita Gurung",
                "phone": "+971 50 234 5678", "email": "sita.gurung@company.com", "nationality": "Nepali", "gender": "female",
                "dept": dept_objs["Operations"], "desig": desig_objs["Field Coordinator"],
                "salary": Decimal("3200.00"), "status": Employee.Status.ACTIVE, "client": "Al Marjan Facility Services",
                "joining_date": date(2024, 8, 15), "passport": "N23456789", "citizenship": "02-04-71-23456",
            },
            {
                "employee_id": "EMP-1003", "first_name": "Bikash", "last_name": "Thapa", "full_name": "Bikash Thapa",
                "phone": "+971 50 345 6789", "email": "bikash.thapa@company.com", "nationality": "Nepali", "gender": "male",
                "dept": dept_objs["Logistics & Fleet"], "desig": desig_objs["Fleet Driver"],
                "salary": Decimal("2600.00"), "status": Employee.Status.ACTIVE, "client": "Global Freight Dubai",
                "joining_date": date(2024, 11, 1), "passport": "N34567890", "citizenship": "03-01-70-34567",
            },
            {
                "employee_id": "EMP-1004", "first_name": "Sunil", "last_name": "Shrestha", "full_name": "Sunil Shrestha",
                "phone": "+971 50 456 7890", "email": "sunil.shrestha@company.com", "nationality": "Nepali", "gender": "male",
                "dept": dept_objs["Operations"], "desig": desig_objs["Operations Supervisor"],
                "salary": Decimal("4500.00"), "status": Employee.Status.ACTIVE, "client": "Palm Hospitality LLC",
                "joining_date": date(2023, 6, 1), "passport": "N45678901", "citizenship": "04-03-69-45678",
            },
            {
                "employee_id": "EMP-1005", "first_name": "Pooja", "last_name": "Sharma", "full_name": "Pooja Sharma",
                "phone": "+971 50 567 8901", "email": "pooja.sharma@company.com", "nationality": "Indian", "gender": "female",
                "dept": dept_objs["Human Resources"], "desig": desig_objs["Senior HR Specialist"],
                "salary": Decimal("5200.00"), "status": Employee.Status.ACTIVE, "client": "Internal OMS HQ",
                "joining_date": date(2023, 1, 10), "passport": "Z11223344", "citizenship": "IND-889900",
            },
            {
                "employee_id": "EMP-1006", "first_name": "Mohammad", "last_name": "Tariq", "full_name": "Mohammad Tariq",
                "phone": "+971 50 678 9012", "email": "m.tariq@company.com", "nationality": "Pakistani", "gender": "male",
                "dept": dept_objs["Logistics & Fleet"], "desig": desig_objs["Warehouse Associate"],
                "salary": Decimal("2200.00"), "status": Employee.Status.ON_LEAVE, "client": "Jebel Ali Distribution",
                "joining_date": date(2024, 2, 20), "passport": "PK987654", "citizenship": "42101-1234567-1",
            },
            {
                "employee_id": "EMP-1007", "first_name": "Rohan", "last_name": "Karki", "full_name": "Rohan Karki",
                "phone": "+971 50 789 0123", "email": "rohan.karki@company.com", "nationality": "Nepali", "gender": "male",
                "dept": dept_objs["Hospitality Services"], "desig": desig_objs["Barista"],
                "salary": Decimal("2400.00"), "status": Employee.Status.ACTIVE, "client": "Dubai Marina Cafe",
                "joining_date": date(2025, 1, 5), "passport": "N56789012", "citizenship": "05-02-74-56789",
            },
            {
                "employee_id": "EMP-1008", "first_name": "Kamala", "last_name": "Adhikari", "full_name": "Kamala Adhikari",
                "phone": "+971 50 890 1234", "email": "kamala.adhikari@company.com", "nationality": "Nepali", "gender": "female",
                "dept": dept_objs["Human Resources"], "desig": desig_objs["Visa & PRO Officer"],
                "salary": Decimal("3800.00"), "status": Employee.Status.ACTIVE, "client": "Internal OMS HQ",
                "joining_date": date(2024, 5, 12), "passport": "N67890123", "citizenship": "06-01-73-67890",
            },
            {
                "employee_id": "EMP-1009", "first_name": "Arjun", "last_name": "Tamang", "full_name": "Arjun Tamang",
                "phone": "+971 50 901 2345", "email": "arjun.tamang@company.com", "nationality": "Nepali", "gender": "male",
                "dept": dept_objs["Logistics & Fleet"], "desig": desig_objs["Fleet Driver"],
                "salary": Decimal("2700.00"), "status": Employee.Status.ACTIVE, "client": "Cedar Logistics Transport",
                "joining_date": date(2024, 9, 1), "passport": "N78901234", "citizenship": "07-04-75-78901",
            },
            {
                "employee_id": "EMP-1010", "first_name": "Nisha", "last_name": "Magar", "full_name": "Nisha Magar",
                "phone": "+971 50 012 3456", "email": "nisha.magar@company.com", "nationality": "Nepali", "gender": "female",
                "dept": dept_objs["Hospitality Services"], "desig": desig_objs["Kitchen Assistant"],
                "salary": Decimal("1900.00"), "status": Employee.Status.PENDING, "client": "Al Barsha Catering",
                "joining_date": date(2026, 11, 1), "passport": "N89012345", "citizenship": "08-03-76-89012",
            },
            {
                "employee_id": "EMP-1011", "first_name": "Dipesh", "last_name": "Bhandari", "full_name": "Dipesh Bhandari",
                "phone": "+971 50 112 2334", "email": "dipesh.b@company.com", "nationality": "Nepali", "gender": "male",
                "dept": dept_objs["Operations"], "desig": desig_objs["Field Coordinator"],
                "salary": Decimal("3100.00"), "status": Employee.Status.ACTIVE, "client": "Downtown Facilities Group",
                "joining_date": date(2024, 7, 20), "passport": "N90123456", "citizenship": "09-02-77-90123",
            },
            {
                "employee_id": "EMP-1012", "first_name": "Deepak", "last_name": "Chaudhary", "full_name": "Deepak Chaudhary",
                "phone": "+971 50 223 3445", "email": "deepak.c@company.com", "nationality": "Nepali", "gender": "male",
                "dept": dept_objs["Hospitality Services"], "desig": desig_objs["Kitchen Assistant"],
                "salary": Decimal("1850.00"), "status": Employee.Status.COMPLETED, "client": "Cedar Logistics Dining",
                "joining_date": date(2023, 2, 1), "passport": "N01234567", "citizenship": "10-01-68-01234",
            },
        ]

        emp_objs = []
        for d in employees_data:
            emp, created = Employee.objects.update_or_create(
                employee_id=d["employee_id"],
                defaults={
                    "first_name": d["first_name"],
                    "last_name": d["last_name"],
                    "full_name": d["full_name"],
                    "phone": d["phone"],
                    "email": d["email"],
                    "nationality": d["nationality"],
                    "gender": d["gender"],
                    "department": d["dept"],
                    "designation": d["desig"],
                    "job_title": d["desig"].name,
                    "salary": d["salary"],
                    "status": d["status"],
                    "client_name": d["client"],
                    "joining_date": d["joining_date"],
                    "passport_number": d["passport"],
                    "citizenship_number": d["citizenship"],
                    "work_location": "Dubai, UAE",
                    "emergency_contact_name": "Hari " + d["last_name"],
                    "emergency_contact_relationship": "Parent / Sibling",
                    "emergency_contact_phone": "+977 9800000000",
                    "created_by": admin_user,
                }
            )
            emp_objs.append(emp)

        # 6. Hiring Records (Dubai Joining Forms)
        for emp in emp_objs[:4]:
            HiringRecord.objects.get_or_create(
                employee=emp,
                defaults={
                    "client_name": emp.client_name,
                    "hiring_person_name": "Mina Shrestha",
                    "hiring_person_employee_id": "HR-002",
                    "application_date": emp.joining_date - timedelta(days=30),
                    "joining_date": emp.joining_date,
                    "father_name": "Ram " + emp.last_name,
                    "nationality": emp.nationality,
                    "city": "Kathmandu",
                    "visa_status": "Employment Visa Issued",
                    "visa_expiry": emp.joining_date + timedelta(days=700),
                    "passport_number": emp.passport_number,
                    "citizenship_number": emp.citizenship_number,
                    "passport_expiry": emp.joining_date + timedelta(days=1800),
                    "mobile_number": emp.phone,
                    "whatsapp_number": emp.phone,
                    "basic_salary": emp.salary,
                    "commission_percent": Decimal("3.50"),
                    "allowance": "Transport & Food Provided",
                    "room_provided": True,
                    "training_period": "1 Month",
                    "starting_date": emp.joining_date,
                    "end_date": emp.joining_date + timedelta(days=730),
                    "monthly_target": Decimal("5000.00"),
                    "visa_charges": Decimal("1500.00"),
                    "job_title": emp.job_title,
                    "hr_name": "Mina Shrestha",
                    "hr_phone": "+971 50 222 0002",
                    "assigned_employee_number": emp.employee_id,
                    "status": HiringRecord.Status.CONFIRMED,
                    "created_by": hr_user,
                }
            )

        # 7. Expenses
        expenses_data = [
            ("EXP-2026-001", emp_objs[0], dept_objs["Hospitality Services"], cat_objs["Meals & Catering"], "Metro Catering Supplies", "Kitchen staples and pantry refill", Decimal("1450.00"), date(2026, 10, 1), ExpenseRecord.Status.APPROVED, ExpenseRecord.PaymentMethod.BANK_TRANSFER),
            ("EXP-2026-002", emp_objs[2], dept_objs["Logistics & Fleet"], cat_objs["Transportation & Fuel"], "Emarat Petroleum", "Fleet vehicle fuel cards for October", Decimal("2200.00"), date(2026, 10, 2), ExpenseRecord.Status.PAID, ExpenseRecord.PaymentMethod.CREDIT_CARD),
            ("EXP-2026-003", emp_objs[4], dept_objs["Human Resources"], cat_objs["Visa & Immigration"], "Amer Government Services", "Medical test and Emirates ID renewals", Decimal("3400.00"), date(2026, 9, 28), ExpenseRecord.Status.APPROVED, ExpenseRecord.PaymentMethod.BANK_TRANSFER),
            ("EXP-2026-004", None, dept_objs["Operations"], cat_objs["Office Supplies"], "Al Furjan Stationery", "Quarterly printing paper, toners, and binders", Decimal("780.00"), date(2026, 10, 3), ExpenseRecord.Status.PENDING, ExpenseRecord.PaymentMethod.CASH),
            ("EXP-2026-005", emp_objs[1], dept_objs["Operations"], cat_objs["Accommodation & Utilities"], "DEWA Dubai", "Camp electricity and water utility bill", Decimal("1890.50"), date(2026, 9, 25), ExpenseRecord.Status.PAID, ExpenseRecord.PaymentMethod.ONLINE),
            ("EXP-2026-006", emp_objs[3], dept_objs["Operations"], cat_objs["Equipment & Maintenance"], "Gulf Safety Equipment", "Hi-vis safety vests and work boots", Decimal("1120.00"), date(2026, 10, 4), ExpenseRecord.Status.SUBMITTED, ExpenseRecord.PaymentMethod.CASH),
        ]

        for ref, emp, dept, cat, vendor, desc, amt, bdate, st, pmethod in expenses_data:
            ExpenseRecord.objects.update_or_create(
                reference_number=ref,
                defaults={
                    "employee": emp,
                    "department": dept,
                    "category_ref": cat,
                    "category": cat.name,
                    "vendor_name": vendor,
                    "description": desc,
                    "amount": amt,
                    "currency": "AED",
                    "bill_date": bdate,
                    "due_date": bdate + timedelta(days=14),
                    "paid_date": bdate + timedelta(days=2) if st == ExpenseRecord.Status.PAID else None,
                    "status": st,
                    "payment_method": pmethod,
                    "approved_by": admin_user if st in [ExpenseRecord.Status.APPROVED, ExpenseRecord.Status.PAID] else None,
                    "approved_at": timezone.now() if st in [ExpenseRecord.Status.APPROVED, ExpenseRecord.Status.PAID] else None,
                    "created_by": finance_user,
                }
            )

        # 8. Billing Records (Client Invoices)
        billing_data = [
            ("INV-2026-001", "Cedar Logistics Dining", emp_objs[0], "Monthly manpower catering deployment (October)", Decimal("8500.00"), date(2026, 10, 1), BillingRecord.Status.SENT),
            ("INV-2026-002", "Al Marjan Facility Services", emp_objs[1], "Facility operations coordination Q3 invoice", Decimal("12400.00"), date(2026, 9, 15), BillingRecord.Status.PAID),
            ("INV-2026-003", "Global Freight Dubai", emp_objs[2], "Fleet driver supply services", Decimal("6800.00"), date(2026, 8, 20), BillingRecord.Status.OVERDUE),
            ("INV-2026-004", "Palm Hospitality LLC", emp_objs[3], "Operations supervision contract milestone", Decimal("9500.00"), date(2026, 10, 2), BillingRecord.Status.DRAFT),
        ]
        for inv_no, client, emp, desc, amt, bdate, st in billing_data:
            BillingRecord.objects.update_or_create(
                invoice_number=inv_no,
                defaults={
                    "client_name": client,
                    "employee": emp,
                    "description": desc,
                    "amount": amt,
                    "currency": "AED",
                    "bill_date": bdate,
                    "due_date": bdate + timedelta(days=30),
                    "payment_date": bdate + timedelta(days=10) if st == BillingRecord.Status.PAID else None,
                    "status": st,
                    "created_by": finance_user,
                }
            )

        # 9. Initial Audit Logs
        AuditLog.objects.get_or_create(
            action=AuditLog.Action.CREATE,
            model_name="System",
            object_id="0",
            object_repr="System initialized and sample database seeded",
            defaults={"user": admin_user, "changes": "Initial seed data loaded"}
        )

        self.stdout.write(self.style.SUCCESS("[OK] Successfully seeded 12+ employees, joinings, expenses, billing records, and roles!"))
