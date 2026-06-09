from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Sum
from django.shortcuts import render, redirect
from django.utils import timezone
from .models import Teacher, TeacherSubject
from core.school_scope import get_scoped_object, require_active_school
from academics.models import Assignment, Class, Result, Subject
from attendance.models import Attendance
from finance.models import Payment
from .scope import get_teacher_assignments, get_teacher_class_names, get_teacher_subject_ids
from datetime import timedelta


def _build_subject_summary(subjects):
    return ", ".join(sorted({subject.name for subject in subjects}))


def _parse_assignment_pairs(school, subject_ids, class_ids):
    if not subject_ids or not class_ids or len(subject_ids) != len(class_ids):
        return []

    assignment_pairs = []
    seen_pairs = set()
    for subject_id, class_id in zip(subject_ids, class_ids):
        subject = Subject.objects.filter(id=subject_id, school=school).first()
        assigned_class = Class.objects.filter(id=class_id, school=school).first()
        if subject is None or assigned_class is None:
            continue

        pair_key = (subject.id, assigned_class.id)
        if pair_key in seen_pairs:
            continue

        seen_pairs.add(pair_key)
        assignment_pairs.append((subject, assigned_class))

    return assignment_pairs


def teacher_list(request):
    school = require_active_school(request)

    teachers = Teacher.objects.select_related('school', 'user').filter(school=school)

    return render(request,
    'teachers/teacher_list.html',
    {'teachers': teachers})


def add_teacher(request):
    school = require_active_school(request)
    classes = Class.objects.filter(school=school).order_by("name")
    subjects = Subject.objects.filter(school=school).order_by("name")

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        subject_ids = request.POST.getlist("assignment_subject[]")
        class_ids = request.POST.getlist("assignment_class[]")

        if User.objects.filter(username=username).exists():
            messages.error(request, "That teacher username already exists.")
            return render(request,'teachers/add_teacher.html', {
                'school': school,
                'classes': classes,
                'subjects': subjects,
            })

        assignment_pairs = _parse_assignment_pairs(school, subject_ids, class_ids)

        if not assignment_pairs:
            messages.error(request, "Invalid subject or class assignment.")
            return render(request,'teachers/add_teacher.html', {
                'school': school,
                'classes': classes,
                'subjects': subjects,
            })

        user = User.objects.create_user(
            username=username,
            email=request.POST.get("email", "").strip(),
            password=password,
        )

        teacher = Teacher.objects.create(
            user=user,
            school=school,
            name=request.POST.get('name'),
            phone=request.POST.get('phone'),
            subject=_build_subject_summary([subject for subject, _ in assignment_pairs])
        )

        for subject, assigned_class in assignment_pairs:
            TeacherSubject.objects.create(
                teacher=teacher,
                subject=subject,
                student_class=assigned_class,
            )

        return redirect('teacher_list')

    return render(request,'teachers/add_teacher.html', {
        'school': school,
        'classes': classes,
        'subjects': subjects,
    })


def edit_teacher(request, id):
    school = require_active_school(request)
    teacher = get_scoped_object(request, Teacher, id=id)
    classes = Class.objects.filter(school=school).order_by("name")
    subjects = Subject.objects.filter(school=school).order_by("name")

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        subject_ids = request.POST.getlist("assignment_subject[]")
        class_ids = request.POST.getlist("assignment_class[]")

        if User.objects.filter(username=username).exclude(id=teacher.user_id).exists():
            messages.error(request, "That teacher username already exists.")
            return render(request, 'teachers/edit_teacher.html', {
                'teacher': teacher,
                'school': school,
                'classes': classes,
                'subjects': subjects,
                'existing_assignments': teacher.teachersubject_set.all(),
            })

        assignment_pairs = _parse_assignment_pairs(school, subject_ids, class_ids)
        if not assignment_pairs:
            messages.error(request, "Add at least one valid subject/class assignment.")
            return render(request, 'teachers/edit_teacher.html', {
                'teacher': teacher,
                'school': school,
                'classes': classes,
                'subjects': subjects,
                'existing_assignments': teacher.teachersubject_set.all(),
            })

        teacher.name = request.POST.get('name')
        teacher.phone = request.POST.get('phone')
        teacher.subject = _build_subject_summary([subject for subject, _ in assignment_pairs])
        teacher.user.username = username
        teacher.user.email = request.POST.get("email", "").strip()
        if password:
            teacher.user.set_password(password)
        teacher.user.save()
        teacher.save()

        teacher.teachersubject_set.all().delete()
        for subject, assigned_class in assignment_pairs:
            TeacherSubject.objects.create(
                teacher=teacher,
                subject=subject,
                student_class=assigned_class,
            )

        messages.success(request, "Teacher updated successfully.")
        return redirect('teacher_list')

    return render(request, 'teachers/edit_teacher.html', {
        'teacher': teacher,
        'school': school,
        'classes': classes,
        'subjects': subjects,
        'existing_assignments': teacher.teachersubject_set.all(),
    })


def delete_teacher(request, id):

    teacher = get_scoped_object(request, Teacher, id=id)
    user = teacher.user
    user.delete()

    return redirect('teacher_list')


def reset_teacher_password(request, id):
    teacher = get_scoped_object(request, Teacher, id=id)

    if request.method == "POST":
        new_password = request.POST.get("password", "").strip()
        if not new_password:
            messages.error(request, "Enter a new password for the teacher account.")
        else:
            teacher.user.set_password(new_password)
            teacher.user.save()
            messages.success(request, f"Password reset for {teacher.name}.")
            return redirect("teacher_list")

    return render(request, "teachers/reset_teacher_password.html", {
        "teacher_account": teacher,
    })


def teacher_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user and hasattr(user, "teacher"):
            login(request, user)
            return redirect("teacher_dashboard")

        messages.error(request, "Teacher login failed.")

    return render(request, "teachers/login.html")


@login_required
def teacher_dashboard(request):
    if not hasattr(request.user, "teacher"):
        messages.error(request, "Only teacher accounts can access that page.")
        return redirect("dashboard")

    teacher = request.user.teacher
    assigned_classes = get_teacher_assignments(teacher)
    assignments = Assignment.objects.filter(teacher=teacher).order_by("-created_at")[:5]
    class_names = get_teacher_class_names(teacher)
    subject_ids = get_teacher_subject_ids(teacher)
    today = timezone.localdate()

    attendance_scope = Attendance.objects.filter(
        school=teacher.school,
        student__current_class__in=class_names,
    )
    attendance_labels = []
    attendance_series = []
    for day_offset in range(4, -1, -1):
        current_day = today - timedelta(days=day_offset)
        day_total = attendance_scope.filter(date=current_day).count()
        day_present = attendance_scope.filter(date=current_day, status="Present").count()
        day_rate = round((day_present / day_total) * 100, 1) if day_total else 0
        attendance_labels.append(current_day.strftime("%a"))
        attendance_series.append(day_rate)

    result_scope = Result.objects.filter(
        school=teacher.school,
        student__current_class__in=class_names,
        subject_id__in=subject_ids,
    )
    exam_performance = (
        result_scope.values("subject__name")
        .annotate(avg_score=Avg("total"))
        .order_by("subject__name")
    )
    result_labels = [item["subject__name"] for item in exam_performance]
    result_series = [round(item["avg_score"] or 0, 1) for item in exam_performance]

    enrollment_scope = (
        teacher.school.student_set.filter(current_class__in=class_names)
        .values("current_class")
        .annotate(total=Count("id"))
        .order_by("current_class")
    )
    enrollment_labels = [item["current_class"] or "Unassigned" for item in enrollment_scope]
    enrollment_series = [item["total"] for item in enrollment_scope]

    fee_scope = Payment.objects.filter(
        school=teacher.school,
        student__current_class__in=class_names,
    )
    fee_labels = []
    fee_series = []
    for month_offset in range(4, -1, -1):
        target_month = today.month - month_offset
        target_year = today.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        monthly_total = fee_scope.filter(
            payment_date__year=target_year,
            payment_date__month=target_month,
        ).aggregate(total=Sum("amount_paid"))["total"] or 0
        fee_labels.append(f"{target_month:02d}/{str(target_year)[-2:]}")
        fee_series.append(monthly_total)

    return render(request, "teachers/dashboard.html", {
        "teacher": teacher,
        "assigned_classes": assigned_classes,
        "assignments": assignments,
        "attendance_chart_labels": attendance_labels,
        "attendance_chart_series": attendance_series,
        "result_chart_labels": result_labels,
        "result_chart_series": result_series,
        "enrollment_chart_labels": enrollment_labels,
        "enrollment_chart_series": enrollment_series,
        "fee_chart_labels": fee_labels,
        "fee_chart_series": fee_series,
        "class_performance": exam_performance,
    })
