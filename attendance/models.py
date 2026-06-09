from django.db import models
from core.models import School
from students.models import Student

class Attendance(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    STATUS = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    )

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS)

    def save(self, *args, **kwargs):
        if self.student_id:
            self.school = self.student.school
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.name} - {self.date}"
