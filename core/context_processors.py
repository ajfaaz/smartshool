from .models import School
from .school_scope import get_active_school


def _resolve_dashboard_url_name(request):
    user = request.user
    portal_role = getattr(request, "portal_role", None)

    if getattr(user, "is_authenticated", False):
        if user.is_superuser:
            return "platform_dashboard"
        if hasattr(user, "principal_profile"):
            return "principal_dashboard"
        if hasattr(user, "exam_officer_profile"):
            return "exam_officer_dashboard"
        if hasattr(user, "teacher"):
            return "teacher_dashboard"
        if hasattr(user, "parent"):
            return "parent_dashboard"

        # Student users authenticate as regular User records keyed by admission number.
        from students.models import Student
        if Student.objects.filter(admission_number=user.username).exists():
            return "student_dashboard"

    if portal_role == "student":
        return "student_dashboard"
    if portal_role == "parent":
        return "parent_dashboard"
    return "dashboard"


def school_context(request):
    if getattr(request.user, "is_authenticated", False) and not request.user.is_superuser:
        available_schools = [request.user.school] if request.user.school else []
    else:
        available_schools = School.objects.order_by("name", "id")

    return {
        "active_school": get_active_school(request),
        "available_schools": available_schools,
        "home_dashboard_url_name": _resolve_dashboard_url_name(request),
    }
