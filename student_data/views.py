from datetime import date
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StudentData


@csrf_exempt
def add_student(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        required_fields = ['institution_id', 'admno', 'student_name', 'student_class', 'div', 'password']

        if isinstance(data, list):
            if not data:
                return JsonResponse({'status': False, 'message': 'Empty data list'}, status=400)

            # Validate all items in the list first
            for i, item in enumerate(data):
                missing = [f for f in required_fields if not item.get(f)]
                if missing:
                    return JsonResponse({
                        'status': False, 
                        'message': f'Row {i+1} is missing required fields: {", ".join(missing)}'
                    }, status=400)

            institution_ids = set(item.get('institution_id') for item in data if item.get('institution_id'))
            if institution_ids:
                StudentData.objects.filter(institution_id__in=institution_ids).delete()

            students = [
                StudentData(
                    institution_id=item.get('institution_id'),
                    admno=item.get('admno'),
                    student_name=item.get('student_name'),
                    student_class=item.get('student_class'),
                    div=item.get('div'),
                    password=item.get('password'),
                    mobile=item.get('mobile'),
                    fathername=item.get('fathername'),
                    mothername=item.get('mothername'),
                    imageurl=item.get('imageurl'),
                    address=item.get('address'),
                    place=item.get('place'),
                    remark=item.get('remark'),
                    refno=item.get('refno')
                ) for item in data
            ]
            StudentData.objects.bulk_create(students)
            return JsonResponse({'status': True, 'message': f'{len(students)} students updated successfully'})
        else:
            # Validate single item
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return JsonResponse({
                    'status': False, 
                    'message': f'Missing required fields: {", ".join(missing)}'
                }, status=400)

            institution_id = data.get('institution_id')
            if institution_id:
                StudentData.objects.filter(institution_id=institution_id).delete()

            student = StudentData.objects.create(
                institution_id=institution_id,
                admno=data.get('admno'),
                student_name=data.get('student_name'),
                student_class=data.get('student_class'),
                div=data.get('div'),
                password=data.get('password'),
                mobile=data.get('mobile'),
                fathername=data.get('fathername'),
                mothername=data.get('mothername'),
                imageurl=data.get('imageurl'),
                address=data.get('address'),
                place=data.get('place'),
                remark=data.get('remark'),
                refno=data.get('refno')
            )
            return JsonResponse({'status': True, 'message': 'Student updated successfully', 'id': student.id})


@csrf_exempt
def get_all_students(request):
    institution_id = request.GET.get('institution_id')
    if not institution_id:
        return JsonResponse({'message': 'institution_id required'}, status=400)

    students = list(
        StudentData.objects.filter(institution_id=institution_id)
        .values(
            'institution_id', 'admno', 'student_name', 'student_class',
            'div', 'password', 'mobile', 'fathername', 'mothername',
            'imageurl', 'address', 'place', 'remark', 'refno'
        ).order_by('student_class', 'div', 'student_name')
    )
    return JsonResponse(students, safe=False)


@csrf_exempt
def get_classes_divisions(request):
    institution_id = request.GET.get('institution_id')
    if not institution_id:
        return JsonResponse({'message': 'institution_id required'}, status=400)

    qs = StudentData.objects.filter(institution_id=institution_id)
    classes = sorted(set(v for v in qs.values_list('student_class', flat=True) if v))
    divisions = sorted(set(v for v in qs.values_list('div', flat=True) if v))

    return JsonResponse({'classes': classes, 'divisions': divisions})


@csrf_exempt
def get_students_by_class_division(request):
    institution_id = request.GET.get('institution_id')
    student_class = request.GET.get('student_class')
    div = request.GET.get('div')

    if not institution_id or not student_class or not div:
        return JsonResponse({'message': 'institution_id, student_class and div are required'}, status=400)

    students = list(
        StudentData.objects.filter(
            institution_id=institution_id,
            student_class=student_class,
            div=div
        ).values(
            'institution_id', 'admno', 'student_name', 'student_class',
            'div', 'password', 'mobile', 'fathername', 'mothername',
            'imageurl', 'address', 'place', 'remark', 'refno'
        ).order_by('student_name')
    )
    return JsonResponse(students, safe=False)
