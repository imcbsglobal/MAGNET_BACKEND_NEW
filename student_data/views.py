from datetime import date

from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StudentData
# Create your views here.

@csrf_exempt
def add_student(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        if isinstance(data, list):
            if not data:
                return JsonResponse({'status': False, 'message': 'Empty data list'}, status=400)
            
            # Get unique client IDs from the list to delete existing records
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
            return JsonResponse({
                'status': True,
                'message': f'{len(students)} students updated successfully'
            })
        else:
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
            return JsonResponse({
                'status': True,
                'message': 'Student updated successfully',
                'id': student.id
            })


    #    hsjnsks