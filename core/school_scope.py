from django.shortcuts import get_object_or_404

from .models import School


ACTIVE_SCHOOL_SESSION_KEY = "active_school_id"


def get_active_school(request):
    if getattr(request.user, "is_authenticated", False) and not request.user.is_superuser:
        user_school = getattr(request.user, "school", None)
        if user_school is not None:
            request.session[ACTIVE_SCHOOL_SESSION_KEY] = user_school.id
            return user_school

    school_id = request.session.get(ACTIVE_SCHOOL_SESSION_KEY)
    school = None

    if school_id:
        school = School.objects.filter(id=school_id).first()

    if school is None:
        school = School.objects.order_by("name", "id").first()
        if school is not None:
            request.session[ACTIVE_SCHOOL_SESSION_KEY] = school.id

    return school


def require_active_school(request):
    school = get_active_school(request)
    if school is None:
        raise School.DoesNotExist("No school has been created yet.")
    return school


def set_active_school(request, school):
    request.session[ACTIVE_SCHOOL_SESSION_KEY] = school.id


def get_scoped_object(request, model, **lookup):
    school = require_active_school(request)
    return get_object_or_404(model, school=school, **lookup)
