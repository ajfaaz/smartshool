from django.db import models
from core.models import School


class Student(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    admission_number = models.CharField(max_length=50)
    current_class = models.CharField(max_length=50)
    email = models.EmailField(blank=True)
    date_of_birth = models.DateField()
    parent_phone = models.CharField(max_length=20)
    profile_picture = models.ImageField(upload_to='student_profiles/', null=True, blank=True)

    @property
    def first_name(self):
        return (self.name or "").split(" ", 1)[0]

    @property
    def last_name(self):
        parts = (self.name or "").split(" ", 1)
        return parts[1] if len(parts) > 1 else ""

    @property
    def student_class(self):
        return self.current_class

    def __str__(self):
        return self.name


from django.contrib.auth.models import User

class Parent(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)

    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    students = models.ManyToManyField(Student, related_name="parents", blank=True)

    phone = models.CharField(max_length=20)
    profile_picture = models.ImageField(upload_to='parent_profiles/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.student_id and not self.school_id:
            self.school = self.student.school
        super().save(*args, **kwargs)

    def linked_students(self):
        linked = self.students.all()
        if linked.exists():
            return linked
        if self.student_id:
            return Student.objects.filter(id=self.student_id)
        return Student.objects.none()

    def __str__(self):
        return self.name
