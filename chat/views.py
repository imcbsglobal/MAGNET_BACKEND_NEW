from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ChatRoom, Message, ChatAttachment, UserOnlineStatus
from teachers_manage.models import Teacher
from student_data.models import StudentData
import json
import os
import boto3
from django.conf import settings
from botocore.exceptions import NoCredentialsError
from rest_framework_simplejwt.authentication import JWTAuthentication

@csrf_exempt
def get_assigned_contacts(request):
    """
    Returns contacts for the chat.
    Optimized to NOT create rooms proactively.
    """
    # Try to extract details from JWT token
    role = None
    user_id = None
    institution_id = None

    try:
        auth = JWTAuthentication()
        header = auth.get_header(request)
        if header:
            raw_token = auth.get_raw_token(header)
            validated_token = auth.get_validated_token(raw_token)
            role = validated_token.get('role')
            user_id = validated_token.get('user_id')
            institution_id = validated_token.get('institution_id')
    except Exception as e:
        print(f"JWT extraction failed: {str(e)}")

    # Fallback to query params if not in JWT or if JWT extraction failed
    if not role:
        role = request.GET.get('role')
    if not user_id:
        user_id = request.GET.get('user_id')
    if not institution_id:
        institution_id = request.GET.get('institution_id')
    
    def clean_val(val):
        if val in [None, '', 'null', 'undefined']:
            return None
        return val

    user_id = clean_val(user_id)
    institution_id = clean_val(institution_id)

    if not role:
        return JsonResponse({'status': False, 'message': 'User role is required'}, status=400)

    try:
        if role == 'teacher':
            if not user_id:
                return JsonResponse({'status': False, 'message': 'Teacher ID missing'}, status=400)
            
            try:
                teacher = Teacher.objects.get(id=user_id)
            except Teacher.DoesNotExist:
                return JsonResponse({'status': False, 'message': 'Teacher not found'}, status=404)

            # Filter students by teacher's assigned class and division
            students = StudentData.objects.filter(
                institution_id=teacher.institution_id,
                student_class=teacher.assigned_class,
                div=teacher.assigned_division
            )
            
            # Get existing rooms for this teacher to show last message/unread
            rooms_dict = {}
            rooms = ChatRoom.objects.filter(teacher_id=user_id).prefetch_related('messages')
            for r in rooms:
                rooms_dict[r.student_id] = r

            # Pre-fetch online status
            online_statuses = {
                status.user_id: status.is_online 
                for status in UserOnlineStatus.objects.filter(user_role='student', user_id__in=[s.id for s in students])
            }

            data = []
            for student in students:
                room = rooms_dict.get(student.id)
                data.append({
                    'id': student.id,
                    'name': (student.student_name or '').strip(),
                    'role': 'student',
                    'class': student.student_class,
                    'div': student.div,
                    'room_id': room.id if room else None,
                    'last_message': room.messages.last().content if (room and room.messages.exists()) else '',
                    'last_message_time': room.updated_at.isoformat() if room else '0001-01-01T00:00:00Z',
                    'unread_count': room.messages.filter(is_read=False, sender_role='student').count() if room else 0,
                    'is_online': online_statuses.get(student.id, False)
                })
            
            # Sort data by last_message_time descending
            data.sort(key=lambda x: x['last_message_time'], reverse=True)
            
            return JsonResponse({'status': True, 'contacts': data})

        elif role == 'parent' or role == 'student':
            if not user_id:
                return JsonResponse({'status': False, 'message': 'Student ID missing'}, status=400)
            
            try:
                student_obj = StudentData.objects.get(id=user_id)
            except StudentData.DoesNotExist:
                return JsonResponse({'status': False, 'message': 'Student not found'}, status=404)

            # Filter teachers assigned to this student's class and division
            teachers = Teacher.objects.filter(
                institution_id=student_obj.institution_id,
                assigned_class=student_obj.student_class,
                assigned_division=student_obj.div
            )
            
            # Get existing rooms
            rooms_dict = {}
            rooms = ChatRoom.objects.filter(student_id=user_id).prefetch_related('messages')
            for r in rooms:
                rooms_dict[r.teacher_id] = r

            # Pre-fetch online status
            online_statuses = {
                status.user_id: status.is_online 
                for status in UserOnlineStatus.objects.filter(user_role='teacher', user_id__in=[t.id for t in teachers])
            }

            data = []
            for teacher in teachers:
                room = rooms_dict.get(teacher.id)
                data.append({
                    'id': teacher.id,
                    'name': teacher.username,
                    'role': 'teacher',
                    'room_id': room.id if room else None,
                    'last_message': room.messages.last().content if (room and room.messages.exists()) else '',
                    'last_message_time': room.updated_at.isoformat() if room else '0001-01-01T00:00:00Z',
                    'unread_count': room.messages.filter(is_read=False, sender_role='teacher').count() if room else 0,
                    'is_online': online_statuses.get(teacher.id, False)
                })
            
            # Sort data by last_message_time descending
            data.sort(key=lambda x: x['last_message_time'], reverse=True)
            
            return JsonResponse({'status': True, 'contacts': data})

    except Exception as e:
        return JsonResponse({'status': False, 'message': str(e)}, status=500)

@csrf_exempt
def get_or_create_room(request):
    """
    Creates or retrieves a chat room when a contact is selected.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            teacher_id = data.get('teacher_id')
            student_id = data.get('student_id')

            # Try to get teacher_id from JWT if not provided or for security
            try:
                auth = JWTAuthentication()
                header = auth.get_header(request)
                if header:
                    raw_token = auth.get_raw_token(header)
                    validated_token = auth.get_validated_token(raw_token)
                    if validated_token.get('role') == 'teacher':
                        teacher_id = validated_token.get('user_id')
                    elif validated_token.get('role') in ['parent', 'student']:
                        student_id = validated_token.get('user_id')
            except Exception:
                pass
            
            if not teacher_id or not student_id:
                return JsonResponse({'status': False, 'message': 'Both teacher_id and student_id are required'}, status=400)

            room, _ = ChatRoom.objects.get_or_create(
                teacher_id=teacher_id,
                student_id=student_id
            )
            return JsonResponse({'status': True, 'room_id': room.id})
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=500)
    return JsonResponse({'status': False, 'message': 'POST required'}, status=405)

@csrf_exempt
def get_chat_history(request, room_id):
    try:
        room = ChatRoom.objects.get(id=room_id)
        messages = room.messages.all().order_by('created_at')
        
        # Try to get role from JWT
        role = None
        try:
            auth = JWTAuthentication()
            header = auth.get_header(request)
            if header:
                raw_token = auth.get_raw_token(header)
                validated_token = auth.get_validated_token(raw_token)
                role = validated_token.get('role')
        except Exception:
            pass

        # Mark messages as read for the recipient
        if not role:
            role = request.GET.get('role')
            
        if role == 'teacher':
            room.messages.filter(sender_role='student', is_read=False).update(is_read=True)
        else:
            room.messages.filter(sender_role='teacher', is_read=False).update(is_read=True)

        data = []
        for msg in messages:
            attachments = []
            for att in msg.attachments.all():
                # Check if file exists on Cloudflare R2 path first
                file_url = ""
                
                # If we have a placeholder or no actual file, use the R2 convention
                if not att.file or str(att.file) == 'r2_placeholder':
                    key = f"chat_attachments/{att.file_name}"
                    file_url = f"{settings.CLOUDFLARE_R2_PUBLIC_URL}/{key}"
                else:
                    file_url = att.file.url
                    if not file_url.startswith('http'):
                        file_url = request.build_absolute_uri(file_url)
                
                attachments.append({
                    'file_url': file_url,
                    'file_name': att.file_name,
                    'file_type': att.file_type
                })
            
            data.append({
                'id': msg.id,
                'sender_id': msg.sender_id,
                'sender_role': msg.sender_role,
                'content': msg.content,
                'created_at': msg.created_at.isoformat(),
                'is_read': msg.is_read,
                'attachments': attachments
            })
        
        return JsonResponse({'status': True, 'messages': data})
    except ChatRoom.DoesNotExist:
        return JsonResponse({'status': False, 'message': 'Room not found'}, status=404)

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def upload_to_r2(file_obj, file_name):
    """
    Uploads a file to Cloudflare R2 bucket.
    """
    try:
        # Cloudflare R2 requires s3v4 signature
        from botocore.client import Config
        
        s3 = boto3.client(
            's3',
            endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT,
            aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
            aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
            region_name='auto',
            config=Config(signature_version='s3v4')
        )

        # Define the key (path in bucket)
        key = f"chat_attachments/{file_name}"
        
        # Read file content
        file_content = file_obj.read()
        content_type = getattr(file_obj, 'content_type', 'application/octet-stream')
        
        # Upload the file using put_object
        s3.put_object(
            Bucket=settings.CLOUDFLARE_R2_BUCKET,
            Key=key,
            Body=file_content,
            ContentType=content_type
        )
        
        # Return the public URL
        return f"{settings.CLOUDFLARE_R2_PUBLIC_URL}/{key}"
    except Exception as e:
        import traceback
        print(f"R2 Upload Error: {str(e)}")
        print(traceback.format_exc())
        return None

@csrf_exempt
def upload_chat_file(request):
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        sender_id = request.POST.get('sender_id')
        sender_role = request.POST.get('sender_role')
        file = request.FILES.get('file')

        # Try to get sender info from JWT
        try:
            auth = JWTAuthentication()
            header = auth.get_header(request)
            if header:
                raw_token = auth.get_raw_token(header)
                validated_token = auth.get_validated_token(raw_token)
                sender_role = validated_token.get('role')
                sender_id = validated_token.get('user_id')
        except Exception:
            pass

        if not all([room_id, sender_id, sender_role, file]):
            return JsonResponse({'status': False, 'message': 'Missing data'}, status=400)

        try:
            # 1. Upload to Cloudflare R2
            # Reset file pointer to beginning before upload
            file.seek(0)
            r2_url = upload_to_r2(file, file.name)
            if not r2_url:
                return JsonResponse({'status': False, 'message': 'Failed to upload to Cloud storage'}, status=500)

            # 2. Create database records
            room = ChatRoom.objects.get(id=room_id)
            
            file_type = file.content_type
            if file_type.startswith('audio/'):
                message_content = "" 
            elif file_type.startswith('image/'):
                message_content = "" 
            else:
                message_content = f"Shared a file: {file.name}"

            message = Message.objects.create(
                room=room,
                sender_id=sender_id,
                sender_role=sender_role,
                content=message_content
            )
            
            # Update room's updated_at
            room.save()
            
            # Save metadata only, we use R2 URL for access
            attachment = ChatAttachment.objects.create(
                message=message,
                file='r2_placeholder', # Use a string placeholder to avoid validation issues
                file_name=file.name,
                file_type=file.content_type
            )
            
            # Manually set a dummy file path or just store the name
            # Since we use r2_url, this model instance is mostly for record keeping
            
            # Broadcast via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'chat_{room_id}',
                {
                    'type': 'chat.message',
                    'message': message.content,
                    'sender_id': int(sender_id),
                    'sender_role': sender_role,
                    'created_at': message.created_at.isoformat(),
                    'id': message.id,
                    'attachments': [{
                        'file_url': r2_url,
                        'file_name': attachment.file_name,
                        'file_type': attachment.file_type
                    }]
                }
            )

            # Send Notification to recipient
            recipient_id = room.student_id if sender_role == 'teacher' else room.teacher_id
            recipient_role = 'student' if sender_role == 'teacher' else 'teacher'
            
            async_to_sync(channel_layer.group_send)(
                f'notify_{recipient_role}_{recipient_id}',
                {
                    'type': 'new_message_notification',
                    'room_id': room.id,
                    'sender_id': int(sender_id),
                    'sender_role': sender_role,
                    'message': message.content or f"Sent a {file_type.split('/')[0]}",
                    'created_at': message.created_at.isoformat()
                }
            )
            
            return JsonResponse({
                'status': True, 
                'message': {
                    'id': message.id,
                    'sender_id': message.sender_id,
                    'sender_role': message.sender_role,
                    'content': message.content,
                    'created_at': message.created_at.isoformat(),
                    'attachments': [{
                        'file_url': r2_url,
                        'file_name': attachment.file_name,
                        'file_type': attachment.file_type
                    }]
                }
            })
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return JsonResponse({'status': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'status': False, 'message': 'Only POST allowed'}, status=405)

@csrf_exempt
def send_bulk_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_ids = data.get('student_ids', [])
            teacher_id = data.get('teacher_id')
            content = data.get('content', '')

            # Try to get teacher_id from JWT
            try:
                auth = JWTAuthentication()
                header = auth.get_header(request)
                if header:
                    raw_token = auth.get_raw_token(header)
                    validated_token = auth.get_validated_token(raw_token)
                    if validated_token.get('role') == 'teacher':
                        teacher_id = validated_token.get('user_id')
            except Exception:
                pass

            if not all([student_ids, teacher_id, content]):
                return JsonResponse({'status': False, 'message': 'Missing data'}, status=400)

            channel_layer = get_channel_layer()
            
            for student_id in student_ids:
                # 1. Get or create room
                room, _ = ChatRoom.objects.get_or_create(
                    teacher_id=teacher_id,
                    student_id=student_id
                )

                # 2. Create message
                message = Message.objects.create(
                    room=room,
                    sender_id=teacher_id,
                    sender_role='teacher',
                    content=content
                )

                # Update room's updated_at
                room.save()

                # 3. Broadcast via WebSocket to the room
                async_to_sync(channel_layer.group_send)(
                    f'chat_{room.id}',
                    {
                        'type': 'chat.message',
                        'message': message.content,
                        'sender_id': int(teacher_id),
                        'sender_role': 'teacher',
                        'created_at': message.created_at.isoformat(),
                        'id': message.id,
                        'attachments': []
                    }
                )

                # 4. Send Notification to student
                async_to_sync(channel_layer.group_send)(
                    f'notify_student_{student_id}',
                    {
                        'type': 'new_message_notification',
                        'room_id': room.id,
                        'sender_id': int(teacher_id),
                        'sender_role': 'teacher',
                        'message': message.content,
                        'created_at': message.created_at.isoformat()
                    }
                )

            return JsonResponse({'status': True, 'message': f'Message sent to {len(student_ids)} students'})
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=500)
    return JsonResponse({'status': False, 'message': 'POST required'}, status=405)
