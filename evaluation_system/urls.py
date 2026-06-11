from django.urls import path
from . import views

urlpatterns = [
    path('evaluations/', views.evaluation_list_create, name='evaluation-list-create'),
    path('evaluations/<int:pk>/', views.evaluation_detail, name='evaluation-detail'),
    path('evaluations/teacher/<int:teacher_id>/', views.teacher_evaluations, name='teacher-evaluations'),
    path('evaluations/teacher/<int:teacher_id>/<str:month>/', views.teacher_month_evaluation, name='teacher-month-evaluation'),
    path('evaluations/save/', views.evaluation_detail, name='evaluation-save'),
]
