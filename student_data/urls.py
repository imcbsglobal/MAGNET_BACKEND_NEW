from django.urls import path
from .views import add_student, get_classes_divisions, get_students_by_class_division, get_all_students

urlpatterns = [
    path('add/', add_student),
    path('classes-divisions/', get_classes_divisions),
    path('students/', get_students_by_class_division),
    path('all-students/', get_all_students),
]