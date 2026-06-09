from django.contrib import admin
from .models import Assignment, Session, Term, Class, Subject, Result
from teachers.models import TeacherSubject

admin.site.register(Result)
admin.site.register(Session)
admin.site.register(Term)
admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(TeacherSubject)
admin.site.register(Assignment)
