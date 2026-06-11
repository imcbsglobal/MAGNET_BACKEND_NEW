from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import TeacherEvaluation
from teachers_manage.models import Teacher
import json

def evaluation_to_dict(evaluation):
    return {
        'id': evaluation.id,
        'teacher_id': evaluation.teacher.id,
        'teacher_username': evaluation.teacher.username,
        'institution_id': evaluation.institution_id,
        'month': evaluation.month,
        'exam_classes_with': evaluation.exam_classes_with,
        'exam_total_classes': evaluation.exam_total_classes,
        'exam_excellent': evaluation.exam_excellent,
        'exam_good': evaluation.exam_good,
        'exam_average': evaluation.exam_average,
        'exam_below_average': evaluation.exam_below_average,
        'notebook_entry': evaluation.notebook_entry,
        'notebook_excellent': evaluation.notebook_excellent,
        'notebook_good': evaluation.notebook_good,
        'notebook_average': evaluation.notebook_average,
        'notebook_below_average': evaluation.notebook_below_average,
        'smartroom_hours': evaluation.smartroom_hours,
        'smartroom_ai': evaluation.smartroom_ai,
        'smartroom_youtube': evaluation.smartroom_youtube,
        'smartroom_creative': evaluation.smartroom_creative,
        'lesson_plan_submitted': evaluation.lesson_plan_submitted,
        'lesson_plan_quality': evaluation.lesson_plan_quality,
        'subject_knowledge_1': evaluation.subject_knowledge_1,
        'subject_knowledge_2': evaluation.subject_knowledge_2,
        'subject_knowledge_3': evaluation.subject_knowledge_3,
        'subject_knowledge_4': evaluation.subject_knowledge_4,
        'subject_knowledge_5': evaluation.subject_knowledge_5,
        'classroom_management': evaluation.classroom_management,
        'activity_based_class': evaluation.activity_based_class,
        'training_1': evaluation.training_1,
        'training_2': evaluation.training_2,
        'training_3': evaluation.training_3,
        'training_4': evaluation.training_4,
        'training_5': evaluation.training_5,
        'english_classroom': evaluation.english_classroom,
        'english_informal': evaluation.english_informal,
        'english_fluency': evaluation.english_fluency,
        'cocurricular_extra': evaluation.cocurricular_extra,
        'cocurricular_reward': evaluation.cocurricular_reward,
        'moral_discipline': evaluation.moral_discipline,
        'moral_uniform': evaluation.moral_uniform,
        'moral_good_deeds': evaluation.moral_good_deeds,
        'created_at': evaluation.created_at,
        'updated_at': evaluation.updated_at,
    }

@csrf_exempt
def evaluation_list_create(request):
    if request.method == 'GET':
        institution_id = request.GET.get('institution_id')
        if institution_id:
            evaluations = TeacherEvaluation.objects.filter(institution_id=institution_id)
        else:
            evaluations = TeacherEvaluation.objects.all()
        return JsonResponse([evaluation_to_dict(e) for e in evaluations], safe=False)

@csrf_exempt
def evaluation_detail(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                evaluation = TeacherEvaluation.objects.get(pk=pk)
                return JsonResponse(evaluation_to_dict(evaluation))
            except TeacherEvaluation.DoesNotExist:
                return JsonResponse({'message': 'Not found'}, status=404)
        else:
            return JsonResponse({'message': 'Teacher ID required'}, status=400)

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            teacher_id = data.get('teacher_id')
            month = data.get('month')

            try:
                teacher = Teacher.objects.get(id=teacher_id)
            except Teacher.DoesNotExist:
                return JsonResponse({'message': 'Teacher not found'}, status=404)

            evaluation, created = TeacherEvaluation.objects.get_or_create(
                teacher=teacher,
                month=month,
                defaults={'institution_id': teacher.institution_id}
            )

            # Update teacher's own fields
            if 'exam_classes_with' in data:
                evaluation.exam_classes_with = data.get('exam_classes_with', 0)
            if 'exam_total_classes' in data:
                evaluation.exam_total_classes = data.get('exam_total_classes', 1)
            if 'exam_excellent' in data:
                evaluation.exam_excellent = data.get('exam_excellent', 0)
            if 'exam_good' in data:
                evaluation.exam_good = data.get('exam_good', 0)
            if 'exam_average' in data:
                evaluation.exam_average = data.get('exam_average', 0)
            if 'exam_below_average' in data:
                evaluation.exam_below_average = data.get('exam_below_average', 0)

            if 'notebook_entry' in data:
                evaluation.notebook_entry = data.get('notebook_entry', 0)
            if 'notebook_excellent' in data:
                evaluation.notebook_excellent = data.get('notebook_excellent', 0)
            if 'notebook_good' in data:
                evaluation.notebook_good = data.get('notebook_good', 0)
            if 'notebook_average' in data:
                evaluation.notebook_average = data.get('notebook_average', 0)
            if 'notebook_below_average' in data:
                evaluation.notebook_below_average = data.get('notebook_below_average', 0)

            if 'smartroom_hours' in data:
                evaluation.smartroom_hours = data.get('smartroom_hours', 0)
            if 'smartroom_ai' in data:
                evaluation.smartroom_ai = data.get('smartroom_ai', 0)
            if 'smartroom_youtube' in data:
                evaluation.smartroom_youtube = data.get('smartroom_youtube', 0)
            if 'smartroom_creative' in data:
                evaluation.smartroom_creative = data.get('smartroom_creative', 0)

            # Update HOD fields
            if 'lesson_plan_submitted' in data:
                evaluation.lesson_plan_submitted = data.get('lesson_plan_submitted', 0)
            if 'lesson_plan_quality' in data:
                evaluation.lesson_plan_quality = data.get('lesson_plan_quality', 0)
            if 'subject_knowledge_1' in data:
                evaluation.subject_knowledge_1 = data.get('subject_knowledge_1', 0)
            if 'subject_knowledge_2' in data:
                evaluation.subject_knowledge_2 = data.get('subject_knowledge_2', 0)
            if 'subject_knowledge_3' in data:
                evaluation.subject_knowledge_3 = data.get('subject_knowledge_3', 0)
            if 'subject_knowledge_4' in data:
                evaluation.subject_knowledge_4 = data.get('subject_knowledge_4', 0)
            if 'subject_knowledge_5' in data:
                evaluation.subject_knowledge_5 = data.get('subject_knowledge_5', 0)
            if 'classroom_management' in data:
                evaluation.classroom_management = data.get('classroom_management', 0)
            if 'activity_based_class' in data:
                evaluation.activity_based_class = data.get('activity_based_class', 0)
            if 'training_1' in data:
                evaluation.training_1 = data.get('training_1', 0)
            if 'training_2' in data:
                evaluation.training_2 = data.get('training_2', 0)
            if 'training_3' in data:
                evaluation.training_3 = data.get('training_3', 0)
            if 'training_4' in data:
                evaluation.training_4 = data.get('training_4', 0)
            if 'training_5' in data:
                evaluation.training_5 = data.get('training_5', 0)
            if 'english_classroom' in data:
                evaluation.english_classroom = data.get('english_classroom', 0)
            if 'english_informal' in data:
                evaluation.english_informal = data.get('english_informal', 0)
            if 'english_fluency' in data:
                evaluation.english_fluency = data.get('english_fluency', 0)
            if 'cocurricular_extra' in data:
                evaluation.cocurricular_extra = data.get('cocurricular_extra', 0)
            if 'cocurricular_reward' in data:
                evaluation.cocurricular_reward = data.get('cocurricular_reward', 0)
            if 'moral_discipline' in data:
                evaluation.moral_discipline = data.get('moral_discipline', 0)
            if 'moral_uniform' in data:
                evaluation.moral_uniform = data.get('moral_uniform', 0)
            if 'moral_good_deeds' in data:
                evaluation.moral_good_deeds = data.get('moral_good_deeds', 0)

            evaluation.save()
            return JsonResponse(evaluation_to_dict(evaluation), status=200)

        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)


@csrf_exempt
def teacher_evaluations(request, teacher_id):
    if request.method == 'GET':
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            evaluations = TeacherEvaluation.objects.filter(teacher=teacher)
            return JsonResponse([evaluation_to_dict(e) for e in evaluations], safe=False)
        except Teacher.DoesNotExist:
            return JsonResponse({'message': 'Teacher not found'}, status=404)


@csrf_exempt
def teacher_month_evaluation(request, teacher_id, month):
    if request.method == 'GET':
        try:
            teacher = Teacher.objects.get(id=teacher_id)
            evaluation = TeacherEvaluation.objects.get(teacher=teacher, month=month)
            return JsonResponse(evaluation_to_dict(evaluation))
        except Teacher.DoesNotExist:
            return JsonResponse({'message': 'Teacher not found'}, status=404)
        except TeacherEvaluation.DoesNotExist:
            # Return empty/default evaluation if not found
            return JsonResponse({
                'id': None,
                'teacher_id': teacher.id,
                'teacher_username': teacher.username,
                'institution_id': teacher.institution_id,
                'month': month,
                'exam_classes_with': 0,
                'exam_total_classes': 1,
                'exam_excellent': 0,
                'exam_good': 0,
                'exam_average': 0,
                'exam_below_average': 0,
                'notebook_entry': 0,
                'notebook_excellent': 0,
                'notebook_good': 0,
                'notebook_average': 0,
                'notebook_below_average': 0,
                'smartroom_hours': 0,
                'smartroom_ai': 0,
                'smartroom_youtube': 0,
                'smartroom_creative': 0,
                'lesson_plan_submitted': 0,
                'lesson_plan_quality': 0,
                'subject_knowledge_1': 0,
                'subject_knowledge_2': 0,
                'subject_knowledge_3': 0,
                'subject_knowledge_4': 0,
                'subject_knowledge_5': 0,
                'classroom_management': 0,
                'activity_based_class': 0,
                'training_1': 0,
                'training_2': 0,
                'training_3': 0,
                'training_4': 0,
                'training_5': 0,
                'english_classroom': 0,
                'english_informal': 0,
                'english_fluency': 0,
                'cocurricular_extra': 0,
                'cocurricular_reward': 0,
                'moral_discipline': 0,
                'moral_uniform': 0,
                'moral_good_deeds': 0,
            })
