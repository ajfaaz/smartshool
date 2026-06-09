from django.contrib.auth.models import User
from django.db import models

class School(models.Model):

    name = models.CharField(max_length=200)

    address = models.TextField()

    phone = models.CharField(max_length=20)

    email = models.EmailField()

    logo = models.ImageField(upload_to='school_logos/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    plan = models.CharField(max_length=50)
    expiry_date = models.DateField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.school.name} - {self.plan}"


class SchoolAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="school_admin_profile")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="admins")

    def __str__(self):
        return f"{self.user.username} - {self.school.name}"


class Principal(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="principal_profile")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="principals")
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} - {self.school.name}"


class ExamOfficer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="exam_officer_profile")
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="exam_officers")
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} - {self.school.name}"


def _get_user_school(user):
    if not getattr(user, "is_authenticated", False):
        return None
    if hasattr(user, "school_admin_profile"):
        return user.school_admin_profile.school
    if hasattr(user, "principal_profile"):
        return user.principal_profile.school
    if hasattr(user, "exam_officer_profile"):
        return user.exam_officer_profile.school
    if hasattr(user, "teacher"):
        return user.teacher.school
    if hasattr(user, "parent"):
        return user.parent.school
    return None


User.add_to_class("school", property(_get_user_school))
