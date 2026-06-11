from django.db import models
from teachers_manage.models import Teacher

class TeacherEvaluation(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='evaluations')
    institution_id = models.CharField(max_length=100)
    month = models.CharField(max_length=7)  # YYYY-MM format

    # Teacher's own entries
    exam_classes_with = models.IntegerField(default=0)
    exam_total_classes = models.IntegerField(default=1)
    exam_excellent = models.IntegerField(default=0)
    exam_good = models.IntegerField(default=0)
    exam_average = models.IntegerField(default=0)
    exam_below_average = models.IntegerField(default=0)

    notebook_entry = models.IntegerField(default=0)  # 0 or 6
    notebook_excellent = models.IntegerField(default=0)
    notebook_good = models.IntegerField(default=0)
    notebook_average = models.IntegerField(default=0)
    notebook_below_average = models.IntegerField(default=0)

    smartroom_hours = models.FloatField(default=0)
    smartroom_ai = models.IntegerField(default=0)
    smartroom_youtube = models.IntegerField(default=0)
    smartroom_creative = models.IntegerField(default=0)

    # HOD's entries
    lesson_plan_submitted = models.IntegerField(default=0)  # 0 or 3
    lesson_plan_quality = models.FloatField(default=0)  # 0,1,1.5,2
    subject_knowledge_1 = models.FloatField(default=0)
    subject_knowledge_2 = models.FloatField(default=0)
    subject_knowledge_3 = models.FloatField(default=0)
    subject_knowledge_4 = models.FloatField(default=0)
    subject_knowledge_5 = models.FloatField(default=0)
    classroom_management = models.IntegerField(default=0)  # 1-5
    activity_based_class = models.IntegerField(default=0)  # 1-5
    training_1 = models.IntegerField(default=0)
    training_2 = models.IntegerField(default=0)
    training_3 = models.IntegerField(default=0)
    training_4 = models.IntegerField(default=0)
    training_5 = models.IntegerField(default=0)
    english_classroom = models.IntegerField(default=0)  # 0,2,4,6,8,10
    english_informal = models.IntegerField(default=0)  # 0,2,4,6,8,10
    english_fluency = models.IntegerField(default=0)  # 0,2,4,6,8,10
    cocurricular_extra = models.IntegerField(default=0)  # 1-5
    cocurricular_reward = models.IntegerField(default=0)  # 1-5
    moral_discipline = models.IntegerField(default=0)  # 1-4
    moral_uniform = models.IntegerField(default=0)  # 1-3
    moral_good_deeds = models.IntegerField(default=0)  # 1-3

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('teacher', 'month')

    def __str__(self):
        return f"{self.teacher.username} - {self.month}"
