from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import JobCategory
import json

@csrf_exempt
def job_category_list_create(request):
    if request.method == 'GET':
        institution_id = request.GET.get('institution_id')
        if institution_id:
            categories = list(JobCategory.objects.filter(institution_id=institution_id).values().order_by('-created_at'))
        else:
            categories = list(JobCategory.objects.all().values().order_by('-created_at'))
        return JsonResponse(categories, safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            institution_id = data.get('institution_id')

            if not name or not institution_id:
                return JsonResponse({'message': 'Missing name or institution_id'}, status=400)

            category = JobCategory.objects.create(name=name, institution_id=institution_id)
            return JsonResponse({
                'id': category.id,
                'name': category.name,
                'institution_id': category.institution_id,
                'created_at': category.created_at
            }, status=201)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

@csrf_exempt
def job_category_detail(request, pk):
    try:
        category = JobCategory.objects.get(pk=pk)
    except JobCategory.DoesNotExist:
        return JsonResponse({'message': 'Not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({
            'id': category.id,
            'name': category.name,
            'institution_id': category.institution_id,
            'created_at': category.created_at
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            if not name:
                return JsonResponse({'message': 'Missing name'}, status=400)
            
            category.name = name
            category.save()
            return JsonResponse({
                'id': category.id,
                'name': category.name,
                'institution_id': category.institution_id,
                'created_at': category.created_at
            })
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    elif request.method == 'DELETE':
        category.delete()
        return JsonResponse({'message': 'Deleted successfully'}, status=200)
