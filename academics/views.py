from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Avg, F
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Assignment, Class, Subject, Result
from .sms import send_result_notification
from students.models import Student
from teachers.models import Teacher, TeacherSubject
from .forms import ResultForm
from core.school_scope import get_scoped_object, require_active_school
from teachers.scope import get_teacher_class_names, get_teacher_subject_ids


def _can_manage_results(request):
    return getattr(request.user, "is_authenticated", False) and (
        request.user.is_superuser
        or hasattr(request.user, "school_admin_profile")
        or hasattr(request.user, "teacher")
        or hasattr(request.user, "exam_officer_profile")
    )


def _can_review_results(request):
    return _can_manage_results(request) or hasattr(request.user, "principal_profile")


def calculate_positions(results):
    totals = {}

    for r in results:
        if r.student not in totals:
            totals[r.student] = 0
        totals[r.student] += r.total or 0

    sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)

    positions = {}
    position = 1

    for student, score in sorted_totals:
        positions[student] = position
        position += 1

    return positions


def class_list(request):
    school = require_active_school(request)
    classes = Class.objects.select_related('school').filter(school=school)
    return render(request, 'academics/class_list.html', {'classes': classes})


def add_class(request):
    school = require_active_school(request)

    if request.method == 'POST':
        name = request.POST.get('name')

        Class.objects.create(
            school=school,
            name=name,
        )

        return redirect('class_list')

    return render(request, 'academics/add_class.html', {'school': school})


def delete_class(request, id):
    cls = get_scoped_object(request, Class, id=id)
    cls.delete()
    return redirect('class_list')


def subject_list(request):
    school = require_active_school(request)
    subjects = Subject.objects.select_related('school').filter(school=school)
    return render(request, 'academics/subject_list.html', {'subjects': subjects})


def add_subject(request):
    school = require_active_school(request)

    if request.method == 'POST':
        name = request.POST.get('name')

        Subject.objects.create(
            school=school,
            name=name
        )

        return redirect('subject_list')

    return render(request, 'academics/add_subject.html', {'school': school})


def delete_subject(request, id):
    subject = get_scoped_object(request, Subject, id=id)
    subject.delete()
    return redirect('subject_list')


def teacher_subject_list(request):
    school = require_active_school(request)

    assignments = TeacherSubject.objects.select_related(
        'school', 'teacher', 'subject', 'student_class'
    ).filter(school=school)

    return render(request,
    'academics/teacher_subject_list.html',
    {'assignments': assignments})


def assign_teacher(request):
    school = require_active_school(request)

    teachers = Teacher.objects.select_related('school').filter(school=school)
    subjects = Subject.objects.select_related('school').filter(school=school)
    classes = Class.objects.select_related('school').filter(school=school)

    if request.method == "POST":
        teacher = get_object_or_404(Teacher, id=request.POST.get('teacher'), school=school)
        subject = get_object_or_404(Subject, id=request.POST.get('subject'), school=school)
        student_class = get_object_or_404(Class, id=request.POST.get('student_class'), school=school)

        TeacherSubject.objects.create(
            teacher=teacher,
            subject=subject,
            student_class=student_class
        )

        return redirect('teacher_subject_list')

    return render(request,
    'academics/assign_teacher.html',
    {
        'teachers': teachers,
        'subjects': subjects,
        'classes': classes
    })


@login_required
def add_result(request):
    if not _can_manage_results(request):
        messages.error(request, "You do not have permission to add results.")
        return redirect("dashboard")

    school = require_active_school(request)
    students_qs = Student.objects.filter(school=school).order_by('name')
    subjects_qs = Subject.objects.filter(school=school).order_by('name')
    if hasattr(request.user, "teacher"):
        students_qs = students_qs.filter(current_class__in=get_teacher_class_names(request.user.teacher))
        subjects_qs = subjects_qs.filter(id__in=get_teacher_subject_ids(request.user.teacher))
    if request.method == "POST":
        form = ResultForm(request.POST)
        form.fields['student'].queryset = students_qs
        form.fields['subject'].queryset = subjects_qs
        if form.is_valid():
            result = form.save(commit=False)
            result.school = school
            result.save()
            send_result_notification(result.student)
            messages.success(request, f"Result saved and parent notified for {result.student.name}.")
            return redirect('result_list')
    else:
        form = ResultForm()
        form.fields['student'].queryset = students_qs
        form.fields['subject'].queryset = subjects_qs

    return render(request, 'academics/add_result.html', {
        'form': form,
        'students': students_qs,
        'subjects': subjects_qs
    })


@login_required
def enter_results(request):
    if not _can_manage_results(request):
        messages.error(request, "You do not have permission to enter results.")
        return redirect("dashboard")

    school = require_active_school(request)
    students = Student.objects.filter(school=school).order_by('name')
    subjects = Subject.objects.filter(school=school).order_by('name')
    if hasattr(request.user, "teacher"):
        students = students.filter(current_class__in=get_teacher_class_names(request.user.teacher))
        subjects = subjects.filter(id__in=get_teacher_subject_ids(request.user.teacher))

    if request.method == "POST":
        student_id = request.POST['student']
        subject_id = request.POST['subject']

        ca1 = int(request.POST['ca1'])
        ca2 = int(request.POST['ca2'])
        exam = int(request.POST['exam'])

        student = get_object_or_404(Student, id=student_id, school=school)
        subject = get_object_or_404(Subject, id=subject_id, school=school)

        Result.objects.create(
            school=school,
            student=student,
            subject=subject,
            ca1=ca1,
            ca2=ca2,
            exam=exam
        )
        send_result_notification(student)
        messages.success(request, f"Result saved and parent notified for {student.name}.")

        return redirect('enter_results')

    return render(request, 'enter_results.html', {
        'students': students,
        'subjects': subjects
    })

@login_required
def result_list(request):
    if not _can_review_results(request):
        messages.error(request, "You do not have permission to view results.")
        return redirect("dashboard")

    school = require_active_school(request)

    results = Result.objects.select_related('student', 'subject').filter(school=school)
    if hasattr(request.user, "teacher"):
        results = results.filter(
            student__current_class__in=get_teacher_class_names(request.user.teacher),
            subject_id__in=get_teacher_subject_ids(request.user.teacher),
        )

    return render(request,
    'academics/result_list.html',
    {
        'results': results,
        'can_add_result': _can_manage_results(request),
        'can_comment_result': hasattr(request.user, "principal_profile"),
    })

def class_positions(request):
    school = require_active_school(request)
    # Efficiently calculate averages using annotation to avoid N+1 queries
    students_with_avg = Student.objects.filter(school=school).annotate(
        avg_score=Avg(F('result__ca1') + F('result__ca2') + F('result__exam'))
    ).order_by('-avg_score')

    rankings = []
    for idx, student in enumerate(students_with_avg, start=1):
        avg = student.avg_score or 0
        rankings.append({
            'student': student,
            'average': round(float(avg), 2),
            'position': idx
        })

    return render(request, 'academics/positions.html', {'rankings': rankings})

def generate_report_pdf(request, student_id):
    school = require_active_school(request)
    # Prefer a direct student lookup, but fall back to a result id so
    # existing /report/<id>/pdf links keep working even if they were built
    # from Result primary keys.
    student = Student.objects.filter(id=student_id, school=school).first()
    if student is None:
        result = get_object_or_404(Result.objects.select_related('student'), id=student_id, school=school)
        student = result.student

    results = Result.objects.filter(student=student, school=school)
    all_results = Result.objects.filter(
        school=school,
        student__current_class=student.current_class
    )
    positions = calculate_positions(all_results)
    student_position = positions.get(student)

    template = get_template('report_pdf.html')

    context = {
        'student': student,
        'results': results,
        'position': student_position
    }

    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('PDF generation error')

    return response


from students.models import Student
from .models import Subject, Result

@login_required
def bulk_result_entry(request):
    if not _can_manage_results(request):
        messages.error(request, "You do not have permission to manage bulk results.")
        return redirect("dashboard")

    school = require_active_school(request)

    students = Student.objects.filter(school=school).order_by('name')
    subjects = Subject.objects.filter(school=school).order_by('name')
    if hasattr(request.user, "teacher"):
        students = students.filter(current_class__in=get_teacher_class_names(request.user.teacher))
        subjects = subjects.filter(id__in=get_teacher_subject_ids(request.user.teacher))

    if request.method == "POST":

        subject_id = request.POST.get("subject")
        subject = get_object_or_404(Subject, id=subject_id, school=school)

        for student in students:

            ca1 = request.POST.get(f"ca1_{student.id}")
            ca2 = request.POST.get(f"ca2_{student.id}")
            exam = request.POST.get(f"exam_{student.id}")

            if ca1 and ca2 and exam:
                ca1 = int(ca1)
                ca2 = int(ca2)
                exam = int(exam)
                total = ca1 + ca2 + exam

                updated = Result.objects.filter(
                    student=student,
                    subject=subject
                ).update(
                    ca1=ca1,
                    ca2=ca2,
                    exam=exam,
                    total=total
                )

                if updated == 0:
                    result = Result.objects.create(
                        school=school,
                        student=student,
                        subject=subject,
                        ca1=ca1,
                        ca2=ca2,
                        exam=exam
                    )
                    send_result_notification(result.student)
                else:
                    send_result_notification(student)

        messages.success(request, "Bulk results saved and parent SMS notifications were triggered.")
        return redirect("bulk_result_entry")

    return render(request, "bulk_result_entry.html", {
        "students": students,
        "subjects": subjects
    })


@login_required
def update_principal_comment(request, result_id):
    if not hasattr(request.user, "principal_profile"):
        messages.error(request, "Only principals can update principal comments.")
        return redirect("result_list")

    school = require_active_school(request)
    result = get_object_or_404(Result, id=result_id, school=school)

    if request.method == "POST":
        result.principal_comment = request.POST.get("principal_comment", "").strip()
        result.save(update_fields=["principal_comment"])
        messages.success(request, f"Principal comment updated for {result.student.name} - {result.subject.name}.")

    return redirect("result_list")

from students.models import Student
from .models import Class
from django.shortcuts import redirect

def promote_students(request):
    school = require_active_school(request)
    students = Student.objects.filter(school=school)

    for student in students:

        current_class = student.current_class

        next_class = None

        if current_class == "JSS1":
            next_class = "JSS2"

        elif current_class == "JSS2":
            next_class = "JSS3"

        elif current_class == "SS1":
            next_class = "SS2"

        if next_class:
            student.current_class = next_class
            student.save()

    return redirect('student_list')


@login_required
def assignment_list(request):
    school = require_active_school(request)

    if hasattr(request.user, "teacher"):
        assignments = Assignment.objects.select_related("subject", "teacher").filter(
            school=school,
            teacher=request.user.teacher
        ).order_by("-created_at")
    else:
        assignments = Assignment.objects.select_related("subject", "teacher").filter(
            school=school
        ).order_by("-created_at")

    return render(request, "academics/assignment_list.html", {
        "assignments": assignments,
    })


@login_required
def create_assignment(request):
    if not hasattr(request.user, "teacher"):
        messages.error(request, "Only teachers can create assignments.")
        return redirect("dashboard")

    teacher = request.user.teacher
    subjects = Subject.objects.filter(
        school=teacher.school,
        id__in=get_teacher_subject_ids(teacher)
    ).order_by("name")

    if request.method == "POST":
        subject = get_object_or_404(
            Subject,
            id=request.POST.get("subject"),
            school=teacher.school
        )
        Assignment.objects.create(
            school=teacher.school,
            teacher=teacher,
            subject=subject,
            title=request.POST.get("title", "").strip(),
            description=request.POST.get("description", "").strip(),
            due_date=request.POST.get("due_date"),
        )
        messages.success(request, "Assignment created successfully.")
        return redirect("assignment_list")

    return render(request, "academics/create_assignment.html", {
        "subjects": subjects,
        "teacher": teacher,
    })

