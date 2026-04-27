from django.urls import path
from . import views

urlpatterns = [
    path('', views.teacher_list_create, name='teacher_list_create'),
    path('<int:pk>/', views.teacher_detail, name='teacher_detail'),
]
