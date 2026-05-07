from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Teacher
import json

def teacher_to_dict(t):
    return {
        'id': t.id,
        'staff_id': t.staff_id,
        'username': t.username,
        'password': t.password,
        'job_category': t.job_category,
        'institution_id': t.institution_id,
        'reg_number': t.reg_number,
        'school_reg_number': t.school_reg_number,
        'address': t.address,
        'pincode': t.pincode,
        'nationality': t.nationality,
        'assigned_class': t.assigned_class,
        'assigned_division': t.assigned_division,
        'created_at': t.created_at,
    }

@csrf_exempt
def teacher_list_create(request):
    if request.method == 'GET':
        institution_id = request.GET.get('institution_id')
        qs = Teacher.objects.filter(institution_id=institution_id) if institution_id else Teacher.objects.all()
        return JsonResponse(list(qs.order_by('-created_at').values()), safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            institution_id = data.get('institution_id')

            if not username or not password or not institution_id:
                return JsonResponse({'message': 'Missing required fields'}, status=400)

            teacher = Teacher.objects.create(
                username=username,
                password=password,
                job_category=data.get('job_category'),
                institution_id=institution_id,
                reg_number=data.get('reg_number'),
                school_reg_number=data.get('school_reg_number'),
                address=data.get('address'),
                pincode=data.get('pincode'),
                nationality=data.get('nationality'),
                assigned_class=data.get('assigned_class'),
                assigned_division=data.get('assigned_division'),
            )
            return JsonResponse(teacher_to_dict(teacher), status=201)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def teacher_detail(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk)
    except Teacher.DoesNotExist:
        return JsonResponse({'message': 'Not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(teacher_to_dict(teacher))

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            teacher.username = data.get('username', teacher.username)
            teacher.password = data.get('password', teacher.password)
            teacher.job_category = data.get('job_category', teacher.job_category)
            teacher.reg_number = data.get('reg_number', teacher.reg_number)
            teacher.school_reg_number = data.get('school_reg_number', teacher.school_reg_number)
            teacher.address = data.get('address', teacher.address)
            teacher.pincode = data.get('pincode', teacher.pincode)
            teacher.nationality = data.get('nationality', teacher.nationality)
            teacher.assigned_class = data.get('assigned_class', teacher.assigned_class)
            teacher.assigned_division = data.get('assigned_division', teacher.assigned_division)
            teacher.save()
            return JsonResponse(teacher_to_dict(teacher))
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    elif request.method == 'DELETE':
        teacher.delete()
        return JsonResponse({'message': 'Deleted successfully'}, status=200)
