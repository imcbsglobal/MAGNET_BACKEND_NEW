from django.urls import path
from .views import add_fee_pending, get_fee_pending, get_all_pending_fees

urlpatterns = [
    path('add/', add_fee_pending),
    path('pending/', get_fee_pending),
    path('all-pending/', get_all_pending_fees),
]