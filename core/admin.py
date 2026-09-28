from django.contrib import admin
from .models import DemoRequest, ExamOfficer, Principal, School, SchoolAdmin, Subscription


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ("school_name", "name", "email", "phone", "role", "created_at")
    search_fields = ("school_name", "name", "email", "phone")
    list_filter = ("created_at",)


admin.site.register(School)
admin.site.register(SchoolAdmin)
admin.site.register(Principal)
admin.site.register(ExamOfficer)
admin.site.register(Subscription)

