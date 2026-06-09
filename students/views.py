from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Parent, Student
from academics.models import Class
from core.school_scope import get_scoped_object, require_active_school
from teachers.scope import get_teacher_class_names
from academics.models import Assignment, Result
from attendance.models import Attendance
from finance.models import Payment


def _sync_student_account(student, password=None, old_username=None):
    target_username = student.admission_number.strip()
    if old_username:
        existing_user = User.objects.filter(username=old_username).first()
    else:
        existing_user = User.objects.filter(username=target_username).first()

    if existing_user:
        existing_user.username = target_username
        existing_user.email = student.email
        if password:
            existing_user.set_password(password)
        existing_user.save()
        return existing_user

    return User.objects.create_user(
        username=target_username,
        email=student.email,
        password=password or "student123",
    )

def student_list(request):
    school = require_active_school(request)
    students = Student.objects.select_related('school').filter(school=school).order_by('current_class', 'name')
    if hasattr(request.user, "teacher"):
        students = students.filter(current_class__in=get_teacher_class_names(request.user.teacher))

    return render(request, 'students/student_list.html', {
        'students': students
    })


def add_student(request):
    school = require_active_school(request)
    classes = Class.objects.filter(school=school).order_by('name')

    if request.method == "POST":
        name = request.POST['name']
        admission_number = request.POST['admission_number']
        current_class = request.POST['current_class']
        email = request.POST.get('email', '').strip()
        parent_phone = request.POST['parent_phone']
        date_of_birth = request.POST['date_of_birth']
        password = request.POST.get('password', '').strip()

        if User.objects.filter(username=admission_number).exists():
            messages.error(request, "A user already exists with that admission number.")
            return render(request, 'students/add_student.html', {
                'classes': classes,
                'school': school
            })

        student = Student.objects.create(
            school=school,
            name=name,
            admission_number=admission_number,
            current_class=current_class,
            email=email,
            date_of_birth=date_of_birth,
            parent_phone=parent_phone
        )
        _sync_student_account(student, password=password or "student123")

        return redirect('student_list')

    return render(request, 'students/add_student.html', {
        'classes': classes,
        'school': school
    })


def reset_student_password(request, id):
    school = require_active_school(request)
    student = get_object_or_404(Student, id=id, school=school)
    user = User.objects.filter(username=student.admission_number).first()

    if user is None:
        user = _sync_student_account(student, password="student123")

    if request.method == "POST":
        new_password = request.POST.get("password", "").strip()
        if not new_password:
            messages.error(request, "Enter a new password for the student account.")
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, f"Password reset for {student.name}.")
            return redirect("student_list")

    return render(request, "students/reset_student_password.html", {
        "student": student,
        "account_username": user.username,
    })


def parent_list(request):
    school = require_active_school(request)
    parents = Parent.objects.select_related("user", "school").prefetch_related("students").filter(school=school).order_by("name")

    return render(request, "students/parent_list.html", {
        "parents": parents,
    })


def add_parent(request):
    school = require_active_school(request)
    students = Student.objects.filter(school=school).order_by("name")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        student_ids = request.POST.getlist("students")

        if User.objects.filter(username=username).exists():
            messages.error(request, "That parent username already exists.")
            return render(request, "students/add_parent.html", {"students": students})

        linked_students = list(Student.objects.filter(school=school, id__in=student_ids))
        if not linked_students:
            messages.error(request, "Select at least one student.")
            return render(request, "students/add_parent.html", {"students": students})

        user = User.objects.create_user(
            username=username,
            email=request.POST.get("email", "").strip(),
            password=password,
        )
        parent = Parent.objects.create(
            school=school,
            user=user,
            name=request.POST.get("name", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            student=linked_students[0],
        )
        parent.students.set(linked_students)
        messages.success(request, "Parent created successfully.")
        return redirect("parent_list")

    return render(request, "students/add_parent.html", {"students": students})


def reset_parent_password(request, id):
    school = require_active_school(request)
    parent = get_object_or_404(Parent, id=id, school=school)

    if request.method == "POST":
        new_password = request.POST.get("password", "").strip()
        if not new_password:
            messages.error(request, "Enter a new password for the parent account.")
        else:
            parent.user.set_password(new_password)
            parent.user.save()
            messages.success(request, f"Password reset for {parent.name}.")
            return redirect("parent_list")

    return render(request, "students/reset_parent_password.html", {
        "parent_account": parent,
    })


def edit_parent(request, id):
    school = require_active_school(request)
    parent = get_object_or_404(Parent.objects.prefetch_related("students"), id=id, school=school)
    students = Student.objects.filter(school=school).order_by("name")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        student_ids = request.POST.getlist("students")

        if User.objects.filter(username=username).exclude(id=parent.user_id).exists():
            messages.error(request, "That parent username already exists.")
            return render(request, "students/edit_parent.html", {
                "parent": parent,
                "students": students,
            })

        linked_students = list(Student.objects.filter(school=school, id__in=student_ids))
        if not linked_students:
            messages.error(request, "Select at least one student.")
            return render(request, "students/edit_parent.html", {
                "parent": parent,
                "students": students,
            })

        parent.name = request.POST.get("name", "").strip()
        parent.phone = request.POST.get("phone", "").strip()
        parent.student = linked_students[0]
        parent.user.username = username
        parent.user.email = request.POST.get("email", "").strip()
        if password:
            parent.user.set_password(password)
        parent.user.save()
        parent.save()
        parent.students.set(linked_students)

        messages.success(request, "Parent updated successfully.")
        return redirect("parent_list")

    return render(request, "students/edit_parent.html", {
        "parent": parent,
        "students": students,
    })


def delete_parent(request, id):
    school = require_active_school(request)
    parent = get_object_or_404(Parent, id=id, school=school)
    parent.user.delete()
    messages.success(request, "Parent deleted successfully.")
    return redirect("parent_list")

def edit_student(request, id):

    school = require_active_school(request)
    student = get_scoped_object(request, Student, id=id)
    classes = Class.objects.filter(school=school).order_by('name')

    if request.method == "POST":
        old_admission_number = student.admission_number

        student.name = request.POST['name']
        student.admission_number = request.POST['admission_number']
        student.current_class = request.POST['current_class']
        student.email = request.POST.get('email', '').strip()
        student.date_of_birth = request.POST['date_of_birth']
        student.parent_phone = request.POST['parent_phone']
        password = request.POST.get('password', '').strip()

        if User.objects.filter(username=student.admission_number).exclude(username=old_admission_number).exists():
            messages.error(request, "A user already exists with that admission number.")
            return render(request,'students/edit_student.html',
            {'student': student, 'classes': classes, 'school': school})

        student.save()
        _sync_student_account(student, password=password or None, old_username=old_admission_number)

        return redirect('student_list')

    return render(request,'students/edit_student.html',
    {'student': student, 'classes': classes, 'school': school})


def delete_student(request, id):

    student = get_scoped_object(request, Student, id=id)
    User.objects.filter(username=student.admission_number).delete()
    student.delete()

    return redirect('student_list')

def report_pdf(request, id):
    student = get_object_or_404(Student, id=id)
    # This is a placeholder for your PDF generation logic (e.g., using ReportLab or WeasyPrint)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="report_{student.admission_number}.pdf"'
    response.write(f"Academic Report for {student.name}")
    return response


from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect


def student_login(request):

    if request.method == "POST":

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user and Student.objects.filter(admission_number=username).exists():
            login(request, user)
            return redirect('student_dashboard')

        messages.error(request, "Invalid username or password.")

    return render(request, 'student_login.html')


from django.contrib.auth.decorators import login_required


@login_required
def student_dashboard(request):
    student = Student.objects.filter(admission_number=request.user.username).first()
    results = Result.objects.filter(student=student).select_related("subject").order_by("subject__name") if student else []
    assignments = Assignment.objects.filter(
        school=student.school,
        teacher__teachersubject__student_class__name=student.current_class
    ).select_related("subject", "teacher").distinct().order_by("due_date")[:6] if student else []
    recent_attendance = Attendance.objects.filter(student=student).order_by("-date")[:6] if student else []
    payment_summary = Payment.objects.filter(student=student).aggregate(total_paid=Sum("amount_paid")) if student else {"total_paid": 0}
    payment_history = Payment.objects.filter(student=student).order_by("-payment_date")[:5] if student else []

    if student:
        present_count = Attendance.objects.filter(student=student, status="Present").count()
        absent_count = Attendance.objects.filter(student=student, status="Absent").count()
    else:
        present_count = 0
        absent_count = 0

    return render(request, 'student_dashboard.html', {
        'portal_role': 'student',
        'student': student,
        'results': results,
        'assignments': assignments,
        'recent_attendance': recent_attendance,
        'present_count': present_count,
        'absent_count': absent_count,
        'payment_total': payment_summary.get("total_paid") or 0,
        'payment_history': payment_history,
    })

def parent_login(request):

    if request.method == "POST":

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user and Parent.objects.filter(user=user).exists():
            login(request, user)
            return redirect('parent_dashboard')

        messages.error(request, "Invalid username or password.")

    return render(request, 'parent_login.html')

from .models import Parent

@login_required
def parent_dashboard(request):

    parent = Parent.objects.prefetch_related("students").get(user=request.user)
    students = parent.linked_students().order_by("name")

    selected_student_id = request.GET.get("student")
    student = students.filter(id=selected_student_id).first() if selected_student_id else students.first()

    if student:
        results = Result.objects.filter(student=student).select_related("subject").order_by("subject__name")
        assignments = Assignment.objects.filter(
            school=student.school,
            teacher__teachersubject__student_class__name=student.current_class
        ).select_related("subject", "teacher").distinct().order_by("due_date")[:6]
        recent_attendance = Attendance.objects.filter(student=student).order_by("-date")[:6]
        present_count = Attendance.objects.filter(student=student, status="Present").count()
        absent_count = Attendance.objects.filter(student=student, status="Absent").count()
        payment_summary = Payment.objects.filter(student=student).aggregate(total_paid=Sum("amount_paid"))
        payment_history = Payment.objects.filter(student=student).order_by("-payment_date")[:5]
    else:
        results = []
        assignments = []
        recent_attendance = []
        present_count = 0
        absent_count = 0
        payment_summary = {"total_paid": 0}
        payment_history = []

    return render(request, 'parent_dashboard.html', {
        'portal_role': 'parent',
        'parent': parent,
        'students': students,
        'student': student,
        'results': results,
        'assignments': assignments,
        'recent_attendance': recent_attendance,
        'present_count': present_count,
        'absent_count': absent_count,
        'payment_total': payment_summary.get("total_paid") or 0,
        'payment_history': payment_history,
    })


from django.shortcuts import render
from .models import Student

def student_id_card(request, student_id):

    student = get_scoped_object(request, Student, id=student_id)

    return render(request, "students/id_card.html", {
        "student": student
    })

