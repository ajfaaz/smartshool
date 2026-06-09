from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'school', 'subject', 'phone')
    list_filter = ('school', 'subject')
    search_fields = ('name', 'phone')
    fields = ('user', 'school', 'name', 'phone', 'subject', 'profile_picture')
    readonly_fields = ('user',)