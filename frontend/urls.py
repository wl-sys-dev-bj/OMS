from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register("employees", views.EmployeeViewSet)
router.register("joinings", views.HiringRecordViewSet)
router.register("documents", views.EmployeeDocumentViewSet)
router.register("billing", views.BillingRecordViewSet)
router.register("expenses", views.ExpenseRecordViewSet)
router.register("expense-categories", views.ExpenseCategoryViewSet)
router.register("expense-products", views.ExpenseProductViewSet)

urlpatterns = [
    path('dashboard/', views.home, name='home'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('documents/<int:pk>/download/', views.employee_document_download, name='employee-document-download'),
    path('joinings/<int:pk>/photo/', views.joining_photo, name='joining-photo'),
] + [path('api/', include(router.urls))]