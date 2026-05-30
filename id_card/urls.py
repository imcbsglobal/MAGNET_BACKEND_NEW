from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.id_card_student_list, name='id_card_student_list'),
    path('send-link/', views.send_id_card_link, name='send_id_card_link'),
    path('bulk-send/', views.bulk_send_id_card_links, name='bulk_send_id_card_links'),
    path('parent-link/', views.parent_link_info, name='parent_link_info'),
    path('submit/', views.submit_id_card_form, name='submit_id_card_form'),
    path('submission/', views.id_card_submission_detail, name='id_card_submission_detail'),
    path('submission/<int:pk>/', views.update_id_card_submission, name='update_id_card_submission'),
]
