from django.urls import path
from . import views

urlpatterns = [
    path('admins/', views.administrator_list_create, name='administrator_list_create'),
    path('admins/<int:pk>/', views.administrator_detail, name='administrator_detail'),
]
