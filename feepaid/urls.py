from django.urls import path
from .views import add_fee_paid, get_fee_paid, get_all_paid_fees

urlpatterns = [
    path('add/', add_fee_paid),
    path('paid/', get_fee_paid),
    path('all-paid/', get_all_paid_fees),
]