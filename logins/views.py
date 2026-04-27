from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from add_administrators.models import AdministratorProfile
from teachers_manage.models import Teacher
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@csrf_exempt
def superadmin_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_superuser:
                    tokens = get_tokens_for_user(user)
                    return JsonResponse({
                        'status': True,
                        'message': 'Superadmin login successful',
                        'role': 'superadmin',
                        **tokens
                    })
                else:
                    return JsonResponse({'status': False, 'message': 'Unauthorized: Not a superuser'}, status=403)
            else:
                return JsonResponse({'status': False, 'message': 'Invalid credentials'}, status=401)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'status': False, 'message': 'Only POST method allowed'}, status=405)

@csrf_exempt
def administrator_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            institution_id = data.get('institution_id')
            username = data.get('username')
            password = data.get('password')

            try:
                administrator = AdministratorProfile.objects.get(institution_id=institution_id, username=username, password=password)
                
                refresh = RefreshToken()
                refresh['user_id'] = administrator.id
                refresh['role'] = 'admin'
                refresh['institution_id'] = administrator.institution_id

                return JsonResponse({
                    'status': True,
                    'message': 'Administrator login successful',
                    'role': 'admin',
                    'institution_id': administrator.institution_id,
                    'school_name': administrator.school_name,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                })
            except AdministratorProfile.DoesNotExist:
                return JsonResponse({'status': False, 'message': 'Invalid Institution ID, Username, or Password'}, status=401)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'status': False, 'message': 'Only POST method allowed'}, status=405)

@csrf_exempt
def teacher_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            institution_id = data.get('institution_id')
            username = data.get('username')
            password = data.get('password')

            try:
                teacher = Teacher.objects.get(institution_id=institution_id, username=username, password=password)
                
                refresh = RefreshToken()
                refresh['user_id'] = teacher.id
                refresh['role'] = 'teacher'
                refresh['institution_id'] = teacher.institution_id

                return JsonResponse({
                    'status': True,
                    'message': 'Teacher login successful',
                    'role': 'teacher',
                    'username': teacher.username,
                    'institution_id': teacher.institution_id,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                })
            except Teacher.DoesNotExist:
                return JsonResponse({'status': False, 'message': 'Invalid Institution ID, Username, or Password'}, status=401)
        except Exception as e:
            return JsonResponse({'status': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'status': False, 'message': 'Only POST method allowed'}, status=405)
