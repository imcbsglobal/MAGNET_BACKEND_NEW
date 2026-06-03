from django.db import models
from teachers_manage.models import Teacher
from student_data.models import StudentData

class ChatRoom(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='chat_rooms')
    student = models.ForeignKey(StudentData, on_delete=models.CASCADE, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('teacher', 'student')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat between {self.teacher.username} and {self.student.student_name}"

class Message(models.Model):
    SENDER_ROLES = [
        ('teacher', 'Teacher'),
        ('student', 'Student/Parent'),
    ]
    
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender_id = models.PositiveIntegerField() # ID from Teacher or StudentData
    sender_role = models.CharField(max_length=20, choices=SENDER_ROLES)
    content = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"From {self.sender_role} ({self.sender_id}) in room {self.room.id}"

class ChatAttachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

class UserOnlineStatus(models.Model):
    user_id = models.PositiveIntegerField()
    user_role = models.CharField(max_length=20) # 'teacher' or 'student'
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user_id', 'user_role')
