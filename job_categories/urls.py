from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_category_list_create, name='job_category_list_create'),
    path('<int:pk>/', views.job_category_detail, name='job_category_detail'),
]
