from django.urls import path
from . import views

urlpatterns = [
    path('students/', views.id_card_student_list, name='id_card_student_list'),
    path('parent-link/', views.parent_link_info, name='parent_link_info'),
    path('lookup-by-phone/', views.lookup_by_phone, name='lookup_by_phone'),
    path('submit/', views.submit_id_card_form, name='submit_id_card_form'),
    path('submit-by-phone/', views.submit_id_card_form_by_phone, name='submit_id_card_form_by_phone'),
    path('upload-photo/', views.upload_student_photo, name='upload_student_photo'),
    path('school-info/', views.id_card_school_info, name='id_card_school_info'),
    path('submission/', views.id_card_submission_detail, name='id_card_submission_detail'),
    path('submission/<int:pk>/', views.update_id_card_submission, name='update_id_card_submission'),
    # PDF generation endpoints
    path('generate-pdf/', views.generate_id_card_pdf, name='generate_id_card_pdf'),
    path('generate-bulk-pdf/', views.generate_bulk_id_card_pdf, name='generate_bulk_id_card_pdf'),
    # Form status management
    path('form-status/', views.id_card_form_status, name='id_card_form_status'),
    path('toggle-form/', views.toggle_id_card_form, name='toggle_id_card_form'),
    # House Groups Master
    path('house-groups/<str:institution_id>/', views.list_house_groups, name='list_house_groups'),
    path('house-groups-add/', views.add_house_group, name='add_house_group'),
    path('house-groups-delete/<int:group_id>/', views.delete_house_group, name='delete_house_group'),
]