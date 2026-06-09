from django.contrib.auth.models import User
from django.db import models
from academics.models import Subject, Class
from core.models import School

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    subject = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='teacher_profiles/', null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def first_name(self):
        return (self.name or "").split(" ", 1)[0]

    @property
    def last_name(self):
        parts = (self.name or "").split(" ", 1)
        return parts[1] if len(parts) > 1 else ""

class TeacherSubject(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    student_class = models.ForeignKey(Class, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.teacher_id:
            self.school = self.teacher.school
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.teacher} - {self.subject} ({self.student_class})"
