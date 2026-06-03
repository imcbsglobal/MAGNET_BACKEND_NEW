from django.urls import path
from . import views

urlpatterns = [
    path('contacts/', views.get_assigned_contacts, name='get_assigned_contacts'),
    path('get-room/', views.get_or_create_room, name='get_or_create_room'),
    path('history/<int:room_id>/', views.get_chat_history, name='get_chat_history'),
    path('upload/', views.upload_chat_file, name='upload_chat_file'),
    path('send-bulk/', views.send_bulk_message, name='send_bulk_message'),
]
