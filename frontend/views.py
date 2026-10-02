import mimetypes

from django.shortcuts import render, redirect
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import (
    BillingRecord,
    Employee,
    EmployeeDocument,
    ExpenseCategory,
    ExpenseProduct,
    ExpenseRecord,
    HiringRecord,
)
from .serializers import (
    BillingRecordSerializer,
    EmployeeDocumentSerializer,
    EmployeeSerializer,
    ExpenseCategorySerializer,
    ExpenseProductSerializer,
    ExpenseRecordSerializer,
    HiringRecordSerializer,
)


class SearchableModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def filter_search(self, queryset, fields):
        search = self.request.query_params.get("search", "").strip()
        if search:
            from django.db.models import Q

            query = Q()
            for field in fields:
                query |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(query)
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class EmployeeViewSet(SearchableModelViewSet):
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.prefetch_related("documents").all()

    def get_queryset(self):
        return self.filter_search(
            super().get_queryset(),
            ["employee_id", "full_name", "phone", "client_name"],
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.joinings.exists():
            raise ValidationError("Employees with joining records cannot be deleted.")
        for document in instance.documents.all():
            document.file.delete(save=False)
        instance.delete()


class HiringRecordViewSet(SearchableModelViewSet):
    serializer_class = HiringRecordSerializer
    queryset = HiringRecord.objects.select_related("employee").all()

    def get_queryset(self):
        return self.filter_search(
            super().get_queryset(),
            ["employee__employee_id", "employee__full_name", "client_name", "hiring_person_name"],
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        if instance.passport_photo:
            instance.passport_photo.delete(save=False)
        instance.delete()


class EmployeeDocumentViewSet(SearchableModelViewSet):
    serializer_class = EmployeeDocumentSerializer
    queryset = EmployeeDocument.objects.select_related("employee").all()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    def perform_destroy(self, instance):
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


class ExpenseRecordViewSet(SearchableModelViewSet):
    serializer_class = ExpenseRecordSerializer
    queryset = ExpenseRecord.objects.prefetch_related("items__product").all()

    def get_queryset(self):
        return self.filter_search(
            super().get_queryset(),
            ["reference_number", "vendor_name", "category", "description"],
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


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

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html')

    return render(request, 'login.html')


@login_required(login_url='login')
def home(request):
    return render(request, 'dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def employee_document_download(request, pk):
    document = get_object_or_404(EmployeeDocument, pk=pk)
    try:
        file_handle = document.file.open("rb")
    except FileNotFoundError as error:
        raise Http404("Document file not found.") from error
    filename = document.title or document.file.name.rsplit("/", 1)[-1]
    return FileResponse(file_handle, as_attachment=True, filename=filename)


@login_required(login_url="login")
def joining_photo(request, pk):
    joining = get_object_or_404(HiringRecord, pk=pk)
    try:
        file_handle = joining.passport_photo.open("rb")
    except (FileNotFoundError, ValueError) as error:
        raise Http404("Passport photo not found.") from error
    content_type = mimetypes.guess_type(joining.passport_photo.name)[0] or "application/octet-stream"
    return FileResponse(file_handle, content_type=content_type)