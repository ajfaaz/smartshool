from django.db import models
from core.models import School

class Session(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Term(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Class(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Subject(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Result(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    ca1 = models.IntegerField()
    ca2 = models.IntegerField()
    exam = models.IntegerField()
    total = models.IntegerField(blank=True, null=True)

    teacher_comment = models.TextField(blank=True, null=True)
    principal_comment = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.student_id:
            self.school = self.student.school
        # Ensure posted values are treated as numbers before computing total.
        self.ca1 = int(self.ca1 or 0)
        self.ca2 = int(self.ca2 or 0)
        self.exam = int(self.exam or 0)
        self.total = self.ca1 + self.ca2 + self.exam
        super().save(*args, **kwargs)

    def grade(self):
        t = self.total or 0
        if t >= 70:
            return "A"
        elif t >= 60:
            return "B"
        elif t >= 50:
            return "C"
        elif t >= 45:
            return "D"
        elif t >= 40:
            return "E"
        else:
            return "F"

    def __str__(self):
        return f"{self.student} - {self.subject}"


class Assignment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.teacher_id:
            self.school = self.teacher.school
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
