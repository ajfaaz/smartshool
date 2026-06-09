from django.contrib import admin
from .models import Student, Parent

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'admission_number', 'school', 'current_class')
    list_filter = ('school', 'current_class')
    search_fields = ('name', 'admission_number', 'email')
    fields = ('school', 'name', 'admission_number', 'current_class', 'email', 'date_of_birth', 'parent_phone', 'profile_picture')

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'phone')
    list_filter = ('school',)
    search_fields = ('name', 'phone', 'email')
    fields = ('user', 'school', 'name', 'phone', 'student', 'students', 'profile_picture')
    readonly_fields = ('user',)
