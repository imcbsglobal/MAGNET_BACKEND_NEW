from django.urls import path
from .views import add_fee_paid

urlpatterns = [
    path('add/', add_fee_paid),
]