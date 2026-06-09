from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Avg, Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.conf import settings
from students.models import Parent, Student
from teachers.models import Teacher
from academics.models import Class, Result, Session, Subject, Term
from attendance.models import Attendance
from finance.models import FeeStructure, Payment
from .models import ExamOfficer, Principal, School, SchoolAdmin, Subscription
from .school_scope import require_active_school, set_active_school


def _ensure_school_management_access(request):
    if (
        hasattr(request.user, "teacher")
        or hasattr(request.user, "principal_profile")
        or hasattr(request.user, "exam_officer_profile")
        or getattr(request, "portal_role", None) in {"student", "parent"}
    ):
        messages.error(request, "That area is available to school administrators only.")
        return False
    return True


FORGOT_PASSWORD_PORTALS = [
    {
        "key": "platform_admin",
        "title": "Platform Admin",
        "description": "Verify with your platform admin email address.",
        "login_url": "platform_login",
        "verification_label": "Email Address",
        "verification_name": "email",
        "verification_type": "email",
        "accent": "dark",
    },
    {
        "key": "school_admin",
        "title": "School Admin",
        "description": "Verify with the email address on the admin account.",
        "login_url": "school_admin_login",
        "verification_label": "Email Address",
        "verification_name": "email",
        "verification_type": "email",
        "accent": "primary",
    },
    {
        "key": "teacher",
        "title": "Teacher",
        "description": "Verify with the teacher phone number on record.",
        "login_url": "teacher_login",
        "verification_label": "Phone Number",
        "verification_name": "phone",
        "verification_type": "text",
        "accent": "success",
    },
    {
        "key": "principal",
        "title": "Principal",
        "description": "Verify with the principal phone number on record.",
        "login_url": "principal_login",
        "verification_label": "Phone Number",
        "verification_name": "phone",
        "verification_type": "text",
        "accent": "secondary",
    },
    {
        "key": "exam_officer",
        "title": "Exam Officer",
        "description": "Verify with the exam officer phone number on record.",
        "login_url": "exam_officer_login",
        "verification_label": "Phone Number",
        "verification_name": "phone",
        "verification_type": "text",
        "accent": "primary",
    },
    {
        "key": "student",
        "title": "Student",
        "description": "Verify with date of birth and parent phone number.",
        "login_url": "student_login",
        "verification_label": "Date of Birth",
        "verification_name": "date_of_birth",
        "verification_type": "date",
        "secondary_label": "Parent Phone",
        "secondary_name": "phone",
        "secondary_type": "text",
        "accent": "warning",
    },
    {
        "key": "parent",
        "title": "Parent",
        "description": "Verify with the parent phone number on record.",
        "login_url": "parent_login",
        "verification_label": "Phone Number",
        "verification_name": "phone",
        "verification_type": "text",
        "accent": "info",
    },
]


def _get_forgot_password_portal(role_key):
    for portal in FORGOT_PASSWORD_PORTALS:
        if portal["key"] == role_key:
            return portal
    return FORGOT_PASSWORD_PORTALS[0]


def _get_portal_account(role_key, username):
    username = (username or "").strip()
    if not username:
        return None, None

    if role_key == "platform_admin":
        user = User.objects.filter(username=username, is_superuser=True).first()
        return user, user.email if user else ""

    if role_key == "school_admin":
        user = User.objects.filter(username=username, school_admin_profile__isnull=False).first()
        return user, user.email if user else ""

    if role_key == "teacher":
        teacher = Teacher.objects.select_related("user").filter(user__username=username).first()
        if teacher:
            return teacher.user, teacher.user.email
        return None, None

    if role_key == "principal":
        principal = Principal.objects.select_related("user").filter(user__username=username).first()
        if principal:
            return principal.user, principal.user.email
        return None, None

    if role_key == "exam_officer":
        exam_officer = ExamOfficer.objects.select_related("user").filter(user__username=username).first()
        if exam_officer:
            return exam_officer.user, exam_officer.user.email
        return None, None

    if role_key == "student":
        student = Student.objects.filter(admission_number=username).first()
        if student:
            user = User.objects.filter(username=student.admission_number).first()
            return user, student.email
        return None, None

    if role_key == "parent":
        parent = Parent.objects.select_related("user").filter(user__username=username).first()
        if parent:
            return parent.user, parent.user.email
        return None, None

    return None, None


def _user_matches_role(user, role_key):
    if user is None:
        return False
    if role_key == "platform_admin":
        return user.is_superuser
    if role_key == "school_admin":
        return hasattr(user, "school_admin_profile")
    if role_key == "teacher":
        return hasattr(user, "teacher")
    if role_key == "principal":
        return hasattr(user, "principal_profile")
    if role_key == "exam_officer":
        return hasattr(user, "exam_officer_profile")
    if role_key == "parent":
        return hasattr(user, "parent")
    if role_key == "student":
        return Student.objects.filter(admission_number=user.username).exists()
    return False


def portals(request):
    portal_items = [
        {
            "title": "Platform Admin",
            "description": "Register schools, create school admins, and manage subscriptions.",
            "url_name": "platform_login",
            "button": "Open Platform Portal",
            "tone": "dark",
        },
        {
            "title": "School Admin",
            "description": "Manage students, teachers, classes, academics, attendance, and finance for one school.",
            "url_name": "school_admin_login",
            "button": "Open School Admin Portal",
            "tone": "primary",
        },
        {
            "title": "Teacher",
            "description": "Access assigned classes, enter results, manage attendance, and create assignments.",
            "url_name": "teacher_login",
            "button": "Open Teacher Portal",
            "tone": "success",
        },
        {
            "title": "Principal",
            "description": "Review school-wide academic results and monitor school performance.",
            "url_name": "principal_login",
            "button": "Open Principal Portal",
            "tone": "secondary",
        },
        {
            "title": "Exam Officer",
            "description": "Manage result entry workflows, quality checks, and publishing controls.",
            "url_name": "exam_officer_login",
            "button": "Open Exam Officer Portal",
            "tone": "primary",
        },
        {
            "title": "Student",
            "description": "View personal dashboard, results, and school records.",
            "url_name": "student_login",
            "button": "Open Student Portal",
            "tone": "warning",
        },
        {
            "title": "Parent",
            "description": "Track your child, view results, and follow school activity from one place.",
            "url_name": "parent_login",
            "button": "Open Parent Portal",
            "tone": "info",
        },
    ]

    return render(request, "core/portals.html", {"portal_items": portal_items})


def forgot_password(request):
    selected_role = request.POST.get("role") or request.GET.get("role") or "student"
    portal = _get_forgot_password_portal(selected_role)
    selected_role = portal["key"]

    if request.method == "POST":
        mode = request.POST.get("mode", "verify")
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        date_of_birth = request.POST.get("date_of_birth", "").strip()
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")
        user, recipient_email = _get_portal_account(selected_role, username)

        if mode == "email":
            if user is None or not _user_matches_role(user, selected_role):
                messages.error(request, "We could not find that account.")
            elif not recipient_email:
                messages.error(request, "No email address is configured for that account yet.")
            else:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_path = reverse("password_reset_confirm", args=[selected_role, uid, token])
                reset_url = request.build_absolute_uri(reset_path)
                send_mail(
                    subject=f"{portal['title']} password reset",
                    message=(
                        f"Hello,\n\nUse the link below to reset your {portal['title']} password:\n"
                        f"{reset_url}\n\nIf you did not request this, you can ignore this email."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    fail_silently=False,
                )
                messages.success(request, f"A reset link has been sent to {recipient_email}.")
                return redirect(f"{reverse('forgot_password')}?role={selected_role}")
        else:
            if selected_role == "platform_admin":
                user = User.objects.filter(
                    username=username,
                    is_superuser=True,
                    email__iexact=email,
                ).first()
            elif selected_role == "school_admin":
                user = User.objects.filter(
                    username=username,
                    school_admin_profile__isnull=False,
                    email__iexact=email,
                ).first()
            elif selected_role == "teacher":
                teacher = Teacher.objects.select_related("user").filter(
                    user__username=username,
                    phone=phone,
                ).first()
                if teacher:
                    user = teacher.user
            elif selected_role == "principal":
                principal = Principal.objects.select_related("user").filter(
                    user__username=username,
                    phone=phone,
                ).first()
                if principal:
                    user = principal.user
            elif selected_role == "exam_officer":
                exam_officer = ExamOfficer.objects.select_related("user").filter(
                    user__username=username,
                    phone=phone,
                ).first()
                if exam_officer:
                    user = exam_officer.user
            elif selected_role == "student":
                student = Student.objects.filter(
                    admission_number=username,
                    date_of_birth=date_of_birth,
                    parent_phone=phone,
                ).first()
                if student:
                    user = User.objects.filter(username=student.admission_number).first()
            elif selected_role == "parent":
                parent = Parent.objects.select_related("user").filter(
                    user__username=username,
                    phone=phone,
                ).first()
                if parent:
                    user = parent.user

            if user is None:
                messages.error(request, "We could not verify that account with the details provided.")
            elif not new_password:
                messages.error(request, "Enter a new password.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, f"Password updated. You can now sign in to the {portal['title']} portal.")
                return redirect(portal["login_url"])

    return render(request, "core/forgot_password.html", {
        "portal_options": FORGOT_PASSWORD_PORTALS,
        "selected_role": selected_role,
        "selected_portal": portal,
    })


def password_reset_confirm(request, role, uidb64, token):
    portal = _get_forgot_password_portal(role)
    role = portal["key"]
    user = None

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    is_valid = user is not None and _user_matches_role(user, role) and default_token_generator.check_token(user, token)

    if request.method == "POST":
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not is_valid:
            messages.error(request, "That password reset link is invalid or has expired.")
        elif not new_password:
            messages.error(request, "Enter a new password.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password reset complete. You can now sign in.")
            return redirect(portal["login_url"])

    return render(request, "core/password_reset_confirm.html", {
        "selected_portal": portal,
        "is_valid_link": is_valid,
        "account_user": user,
    })


def dashboard(request):
    if getattr(request.user, "is_authenticated", False) and request.user.is_superuser:
        return redirect("platform_dashboard")
    if hasattr(request.user, "exam_officer_profile"):
        return redirect("exam_officer_dashboard")

    school = require_active_school(request)
    today = timezone.localdate()
    selected_period = request.GET.get("period", "30d")
    period_options = [
        {"key": "30d", "label": "Last 30 Days"},
        {"key": "90d", "label": "Last 90 Days"},
        {"key": "year", "label": "This Year"},
        {"key": "all", "label": "All Time"},
    ]
    valid_periods = {option["key"] for option in period_options}
    if selected_period not in valid_periods:
        selected_period = "30d"

    date_from = None
    if selected_period == "30d":
        date_from = today - timedelta(days=29)
    elif selected_period == "90d":
        date_from = today - timedelta(days=89)
    elif selected_period == "year":
        date_from = today.replace(month=1, day=1)

    total_students = Student.objects.filter(school=school).count()
    total_teachers = Teacher.objects.filter(school=school).count()
    total_classes = Class.objects.filter(school=school).count()
    total_subjects = Subject.objects.filter(school=school).count()
    attendance_qs = Attendance.objects.filter(school=school)
    payment_qs = Payment.objects.filter(school=school)
    result_qs = Result.objects.filter(school=school)

    if date_from:
        attendance_qs = attendance_qs.filter(date__gte=date_from)
        payment_qs = payment_qs.filter(payment_date__gte=date_from)

    total_attendance = attendance_qs.count()
    present_attendance = attendance_qs.filter(status="Present").count()
    attendance_rate = round((present_attendance / total_attendance) * 100, 1) if total_attendance else 0

    fee_collection = payment_qs.aggregate(total=Sum("amount_paid"))["total"] or 0
    average_result = result_qs.aggregate(score=Avg("total"))["score"] or 0

    attendance_window_start = date_from if date_from else today - timedelta(days=6)
    attendance_days = min((today - attendance_window_start).days + 1, 7)
    attendance_labels = []
    attendance_series = []
    for day_offset in range(attendance_days - 1, -1, -1):
        current_day = today - timedelta(days=day_offset)
        daily_total = attendance_qs.filter(date=current_day).count()
        daily_present = attendance_qs.filter(date=current_day, status="Present").count()
        daily_rate = round((daily_present / daily_total) * 100, 1) if daily_total else 0
        attendance_labels.append(current_day.strftime("%d %b"))
        attendance_series.append(daily_rate)

    monthly_fee_buckets = []
    for month_offset in range(5, -1, -1):
        target_month = today.month - month_offset
        target_year = today.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        monthly_fee_buckets.append((target_year, target_month))

    fee_labels = []
    fee_series = []
    for year_value, month_value in monthly_fee_buckets:
        month_filter = Payment.objects.filter(
            school=school,
            payment_date__year=year_value,
            payment_date__month=month_value,
        )
        if date_from:
            month_filter = month_filter.filter(payment_date__gte=date_from)
        fee_total = month_filter.aggregate(total=Sum("amount_paid"))["total"] or 0
        fee_labels.append(f"{datetime(year_value, month_value, 1).strftime('%b %Y')}")
        fee_series.append(fee_total)

    grade_ranges = [
        ("A", 70, 100),
        ("B", 60, 69),
        ("C", 50, 59),
        ("D", 45, 49),
        ("E", 40, 44),
        ("F", 0, 39),
    ]
    result_labels = []
    result_series = []
    for grade_label, minimum_score, maximum_score in grade_ranges:
        result_labels.append(grade_label)
        result_series.append(
            result_qs.filter(total__gte=minimum_score, total__lte=maximum_score).count()
        )

    enrollment_breakdown = (
        Student.objects.filter(school=school)
        .values("current_class")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    enrollment_labels = [item["current_class"] or "Unassigned" for item in enrollment_breakdown]
    enrollment_series = [item["total"] for item in enrollment_breakdown]

    context = {
        "school": school,
        "selected_period": selected_period,
        "period_options": period_options,
        "selected_period_label": next(option["label"] for option in period_options if option["key"] == selected_period),
        "students": total_students,
        "teachers": total_teachers,
        "classes": total_classes,
        "subjects": total_subjects,
        "attendance_rate": attendance_rate,
        "fee_collection": fee_collection,
        "average_result": round(average_result, 1),
        "filtered_attendance_records": total_attendance,
        "filtered_payment_records": payment_qs.count(),
        "results_are_all_time": True,
        "attendance_chart_labels": attendance_labels,
        "attendance_chart_series": attendance_series,
        "fee_chart_labels": fee_labels,
        "fee_chart_series": fee_series,
        "result_chart_labels": result_labels,
        "result_chart_series": result_series,
        "enrollment_chart_labels": enrollment_labels,
        "enrollment_chart_series": enrollment_series,
    }

    return render(request, "core/dashboard.html", context)


def platform_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user and user.is_superuser:
            login(request, user)
            return redirect("platform_dashboard")

        messages.error(request, "Platform admin login failed.")

    return render(request, "core/platform_login.html")


def school_admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user and getattr(user, "school", None):
            login(request, user)
            set_active_school(request, user.school)
            return redirect("dashboard")

        messages.error(request, "School admin login failed.")

    return render(request, "core/school_admin_login.html")


def principal_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user and hasattr(user, "principal_profile"):
            login(request, user)
            set_active_school(request, user.principal_profile.school)
            return redirect("principal_dashboard")

        messages.error(request, "Principal login failed.")

    return render(request, "core/principal_login.html")


def exam_officer_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user and hasattr(user, "exam_officer_profile"):
            login(request, user)
            set_active_school(request, user.exam_officer_profile.school)
            return redirect("exam_officer_dashboard")

        messages.error(request, "Exam officer login failed.")

    return render(request, "core/exam_officer_login.html")


@login_required
def principal_dashboard(request):
    if not hasattr(request.user, "principal_profile"):
        messages.error(request, "Only principals can access that page.")
        return redirect("dashboard")

    school = request.user.principal_profile.school
    recent_results = Result.objects.select_related("student", "subject").filter(school=school).order_by("-id")[:10]

    return render(request, "core/principal_dashboard.html", {
        "principal": request.user.principal_profile,
        "school": school,
        "recent_results": recent_results,
    })


@login_required
def exam_officer_dashboard(request):
    if not hasattr(request.user, "exam_officer_profile"):
        messages.error(request, "Only exam officers can access that page.")
        return redirect("dashboard")

    school = request.user.exam_officer_profile.school
    recent_results = Result.objects.select_related("student", "subject").filter(school=school).order_by("-id")[:10]

    return render(request, "core/exam_officer_dashboard.html", {
        "exam_officer": request.user.exam_officer_profile,
        "school": school,
        "recent_results": recent_results,
    })


@login_required
def platform_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Only platform admins can access that page.")
        return redirect("dashboard")

    schools = School.objects.order_by("name")
    school_admins = SchoolAdmin.objects.select_related("school", "user").order_by("school__name", "user__username")
    subscriptions = Subscription.objects.select_related("school").order_by("expiry_date", "school__name")

    context = {
        "schools": schools,
        "school_admins": school_admins,
        "subscriptions": subscriptions,
        "total_schools": schools.count(),
        "total_school_admins": school_admins.count(),
        "active_subscriptions": subscriptions.filter(active=True, expiry_date__gte=timezone.now().date()).count(),
    }
    return render(request, "core/platform_dashboard.html", context)


@login_required
def create_school(request):
    if not request.user.is_superuser:
        messages.error(request, "Only platform admins can create schools.")
        return redirect("dashboard")

    if request.method == "POST":
        school = School.objects.create(
            name=request.POST.get("name", "").strip(),
            address=request.POST.get("address", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            email=request.POST.get("email", "").strip(),
        )
        messages.success(request, f"{school.name} created successfully.")

    return redirect("platform_dashboard")


@login_required
def create_school_admin(request):
    if not request.user.is_superuser:
        messages.error(request, "Only platform admins can create school admins.")
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        school = get_object_or_404(School, id=request.POST.get("school"))

        if User.objects.filter(username=username).exists():
            messages.error(request, "That username already exists.")
            return redirect("platform_dashboard")

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=request.POST.get("first_name", "").strip(),
            last_name=request.POST.get("last_name", "").strip(),
            email=request.POST.get("email", "").strip(),
        )
        SchoolAdmin.objects.create(user=user, school=school)
        messages.success(request, f"School admin {username} created for {school.name}.")

    return redirect("platform_dashboard")


@login_required
def create_subscription(request):
    if not request.user.is_superuser:
        messages.error(request, "Only platform admins can manage subscriptions.")
        return redirect("dashboard")

    if request.method == "POST":
        school = get_object_or_404(School, id=request.POST.get("school"))
        Subscription.objects.create(
            school=school,
            plan=request.POST.get("plan", "").strip(),
            expiry_date=request.POST.get("expiry_date"),
            active=bool(request.POST.get("active")),
        )
        messages.success(request, f"Subscription added for {school.name}.")

    return redirect("platform_dashboard")


def switch_school(request):
    if request.method == "POST":
        if getattr(request.user, "is_authenticated", False) and not request.user.is_superuser:
            messages.error(request, "School admins cannot switch away from their assigned school.")
            return redirect(request.POST.get("next") or "dashboard")

        school = School.objects.filter(id=request.POST.get("school")).first()
        if school is not None:
            set_active_school(request, school)
            messages.success(request, f"Active school switched to {school.name}.")
        else:
            messages.error(request, "Selected school was not found.")

    return redirect(request.POST.get("next") or "dashboard")


@login_required
def school_settings(request):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    sessions = Session.objects.filter(school=school).order_by("name")
    terms = Term.objects.filter(school=school).order_by("name")
    fee_structures = FeeStructure.objects.filter(school=school).order_by("class_name", "term")
    classes = Class.objects.filter(school=school).order_by("name")
    principals = Principal.objects.select_related("user").filter(school=school).order_by("name")
    exam_officers = ExamOfficer.objects.select_related("user").filter(school=school).order_by("name")

    return render(request, "core/school_settings.html", {
        "school": school,
        "sessions": sessions,
        "terms": terms,
        "fee_structures": fee_structures,
        "classes": classes,
        "principals": principals,
        "exam_officers": exam_officers,
        "email_backend_label": "SMTP" if settings.EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend" else "Console",
        "email_from_address": settings.DEFAULT_FROM_EMAIL,
        "password_reset_timeout_minutes": settings.PASSWORD_RESET_TIMEOUT // 60,
    })


@login_required
def create_principal(request):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if User.objects.filter(username=username).exists():
            messages.error(request, "That username already exists.")
            return redirect("school_settings")

        user = User.objects.create_user(
            username=username,
            password=password,
            email=request.POST.get("email", "").strip(),
        )
        Principal.objects.create(
            user=user,
            school=school,
            name=request.POST.get("name", "").strip(),
            phone=request.POST.get("phone", "").strip(),
        )
        messages.success(request, "Principal account created.")

    return redirect("school_settings")


@login_required
def create_exam_officer(request):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if User.objects.filter(username=username).exists():
            messages.error(request, "That username already exists.")
            return redirect("school_settings")

        user = User.objects.create_user(
            username=username,
            password=password,
            email=request.POST.get("email", "").strip(),
        )
        ExamOfficer.objects.create(
            user=user,
            school=school,
            name=request.POST.get("name", "").strip(),
            phone=request.POST.get("phone", "").strip(),
        )
        messages.success(request, "Exam officer account created.")

    return redirect("school_settings")


@login_required
def update_school_profile(request):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    if request.method == "POST":
        school.name = request.POST.get("name", "").strip()
        school.address = request.POST.get("address", "").strip()
        school.phone = request.POST.get("phone", "").strip()
        school.email = request.POST.get("email", "").strip()
        if request.FILES.get("logo"):
            school.logo = request.FILES["logo"]
        school.save()
        messages.success(request, "School profile updated.")

    return redirect("school_settings")


@login_required
def create_session(request):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            Session.objects.create(school=school, name=name)
            messages.success(request, "Session added.")
    return redirect("school_settings")


@login_required
def delete_session(request, id):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    session = get_object_or_404(Session, id=id, school=school)
    session.delete()
    messages.success(request, "Session deleted.")
    return redirect("school_settings")


@login_required
def create_term(request):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            Term.objects.create(school=school, name=name)
            messages.success(request, "Term added.")
    return redirect("school_settings")


@login_required
def delete_term(request, id):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    term = get_object_or_404(Term, id=id, school=school)
    term.delete()
    messages.success(request, "Term deleted.")
    return redirect("school_settings")


@login_required
def create_fee_structure(request):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    if request.method == "POST":
        class_name = request.POST.get("class_name", "").strip()
        term = request.POST.get("term", "").strip()
        amount = request.POST.get("amount", "").strip()
        if class_name and term and amount:
            FeeStructure.objects.create(
                school=school,
                class_name=class_name,
                term=term,
                amount=int(amount),
            )
            messages.success(request, "Fee structure saved.")
    return redirect("school_settings")


@login_required
def delete_fee_structure(request, id):
    if not _ensure_school_management_access(request):
        return redirect("dashboard")

    school = require_active_school(request)
    fee_structure = get_object_or_404(FeeStructure, id=id, school=school)
    fee_structure.delete()
    messages.success(request, "Fee structure deleted.")
    return redirect("school_settings")


@login_required
def account_settings(request):
    """
    Display and manage user account settings including profile and password.
    """
    # Handle profile picture upload
    if request.method == "POST" and request.FILES.get("profile_picture"):
        if hasattr(request.user, "teacher"):
            teacher = request.user.teacher
            teacher.profile_picture = request.FILES["profile_picture"]
            teacher.save()
            messages.success(request, "Profile picture updated successfully!")
        elif hasattr(request.user, "parent"):
            parent = request.user.parent
            parent.profile_picture = request.FILES["profile_picture"]
            parent.save()
            messages.success(request, "Profile picture updated successfully!")
        elif Student.objects.filter(admission_number=request.user.username).exists():
            student = Student.objects.get(admission_number=request.user.username)
            student.profile_picture = request.FILES["profile_picture"]
            student.save()
            messages.success(request, "Profile picture updated successfully!")
        
        return redirect("account_settings")
    
    # Get user's role for context
    user_role = None
    profile_obj = None
    
    if request.user.is_superuser:
        user_role = "Platform Admin"
    elif hasattr(request.user, "school_admin_profile"):
        user_role = "School Admin"
    elif hasattr(request.user, "teacher"):
        user_role = "Teacher"
        profile_obj = request.user.teacher
    elif hasattr(request.user, "principal_profile"):
        user_role = "Principal"
    elif hasattr(request.user, "exam_officer_profile"):
        user_role = "Exam Officer"
    elif hasattr(request.user, "parent"):
        user_role = "Parent"
        profile_obj = request.user.parent
    elif Student.objects.filter(admission_number=request.user.username).exists():
        user_role = "Student"
        profile_obj = Student.objects.get(admission_number=request.user.username)
    
    context = {
        "user_role": user_role,
        "profile_obj": profile_obj,
    }
    
    return render(request, "core/account_settings.html", context)


@login_required
def change_password(request):
    """
    Change user password with validation of current password and password strength.
    """
    password_errors = []
    
    if request.method == "POST":
        current_password = request.POST.get("current_password", "")
        new_password = request.POST.get("new_password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not request.user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
        elif not new_password:
            messages.error(request, "New password cannot be empty.")
        elif new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        else:
            # Validate password strength using Django validators
            try:
                validate_password(new_password, user=request.user)
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Password changed successfully.")
                return redirect("account_settings")
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)

    return render(request, "core/change_password.html", {"password_errors": password_errors})


@login_required
def logout_view(request):
    """
    Logs out the user and redirects them back to the specific login portal 
    they belong to based on their account type.
    """
    user = request.user
    target_url = "portals"

    # Identify the user's role before clearing the session to determine the redirect
    if user.is_superuser:
        target_url = "platform_login"
    elif hasattr(user, "school_admin_profile"):
        target_url = "school_admin_login"
    elif hasattr(user, "teacher"):
        target_url = "teacher_login"
    elif hasattr(user, "principal_profile"):
        target_url = "principal_login"
    elif hasattr(user, "exam_officer_profile"):
        target_url = "exam_officer_login"
    elif hasattr(user, "parent"):
        target_url = "parent_login"
    elif Student.objects.filter(admission_number=user.username).exists():
        target_url = "student_login"

    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect(target_url)
