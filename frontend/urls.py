from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.home, name='home'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
   
]