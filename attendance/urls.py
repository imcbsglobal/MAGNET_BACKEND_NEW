from django.urls import path
from . import views

urlpatterns = [
    path('save/', views.save_attendance),
    path('get/', views.get_attendance),
]
