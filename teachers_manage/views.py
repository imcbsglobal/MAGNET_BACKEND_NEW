from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Teacher
import json

@csrf_exempt
def teacher_list_create(request):
    if request.method == 'GET':
        institution_id = request.GET.get('institution_id')
        if institution_id:
            teachers = list(Teacher.objects.filter(institution_id=institution_id).values().order_by('-created_at'))
        else:
            teachers = list(Teacher.objects.all().values().order_by('-created_at'))
        return JsonResponse(teachers, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            job_category = data.get('job_category')
            institution_id = data.get('institution_id')

            if not username or not password or not institution_id:
                return JsonResponse({'message': 'Missing required fields'}, status=400)

            teacher = Teacher.objects.create(username=username, password=password, job_category=job_category, institution_id=institution_id)
            return JsonResponse({
                'id': teacher.id,
                'username': teacher.username,
                'job_category': teacher.job_category,
                'institution_id': teacher.institution_id,
                'created_at': teacher.created_at
            }, status=201)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def teacher_detail(request, pk):
    try:
        teacher = Teacher.objects.get(pk=pk)
    except Teacher.DoesNotExist:
        return JsonResponse({'message': 'Not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'id': teacher.id,
            'username': teacher.username,
            'job_category': teacher.job_category,
            'institution_id': teacher.institution_id,
            'created_at': teacher.created_at
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            teacher.username = data.get('username', teacher.username)
            teacher.password = data.get('password', teacher.password)
            teacher.job_category = data.get('job_category', teacher.job_category)
            teacher.save()
            return JsonResponse({
                'id': teacher.id,
                'username': teacher.username,
                'job_category': teacher.job_category,
                'institution_id': teacher.institution_id,
                'created_at': teacher.created_at
            })
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    elif request.method == 'DELETE':
        teacher.delete()
        return JsonResponse({'message': 'Deleted successfully'}, status=200)
