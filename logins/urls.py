from django.urls import path
from . import views

urlpatterns = [
    path('superadmin-login/', views.superadmin_login, name='superadmin_login'),
    path('admin-login/', views.administrator_login, name='admin_login'),
    path('user-login/', views.teacher_login, name='teacher_login'),
]
