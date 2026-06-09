from django.contrib import admin
from .models import ExamOfficer, Principal, School, SchoolAdmin, Subscription


admin.site.register(School)
admin.site.register(SchoolAdmin)
admin.site.register(Principal)
admin.site.register(ExamOfficer)
admin.site.register(Subscription)
