from django.db import models
from core.models import School
from students.models import Student


class FeeStructure(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    class_name = models.CharField(max_length=100)

    term = models.CharField(max_length=50)

    amount = models.IntegerField()

    def __str__(self):
        return f"{self.class_name} - {self.term}"


class Payment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount_paid = models.IntegerField()
    term = models.CharField(max_length=20)
    payment_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20)
    reference = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if self.student_id:
            self.school = self.student.school
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.student)


class FeePayment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    reference = models.CharField(max_length=200)

    status = models.CharField(max_length=20)

    date = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.student_id:
            self.school = self.student.school
        super().save(*args, **kwargs)



   
    

  
