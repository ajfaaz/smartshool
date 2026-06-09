from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from students.models import Student
from academics.models import Term
from .models import Attendance
from datetime import date, timedelta
from core.school_scope import require_active_school
from teachers.scope import get_teacher_class_names


def mark_attendance(request):
    school = require_active_school(request)
    today = date.today()
    selected_date = today
    selected_class_name = None
    selected_term = None
    search_query = ""

    student_qs = Student.objects.select_related('school').filter(school=school)
    if hasattr(request.user, "teacher"):
        allowed_classes = list(get_teacher_class_names(request.user.teacher))
        student_qs = student_qs.filter(current_class__in=allowed_classes)
    else:
        allowed_classes = list(student_qs.order_by('current_class').values_list('current_class', flat=True).distinct())

    class_names = list(student_qs.order_by('current_class').values_list('current_class', flat=True).distinct())
    if request.method == "POST":
        selected_class_name = request.POST.get("class_name")
        selected_date = parse_date(request.POST.get("date") or today.isoformat()) or today
        selected_term = request.POST.get("term")
        search_query = request.POST.get("search", "").strip()

        if selected_class_name:
            student_qs = student_qs.filter(current_class=selected_class_name)

        if search_query:
            student_qs = student_qs.filter(
                Q(name__icontains=search_query) | Q(admission_number__icontains=search_query)
            )

        students = student_qs.order_by('name')
        for student in students:
            status = request.POST.get(f"student_{student.id}")
            if status not in {"Present", "Absent", "Late"}:
                continue

            Attendance.objects.update_or_create(
                student=student,
                date=selected_date,
                defaults={
                    "status": status,
                    "school": school,
                },
            )

        messages.success(request, "Attendance saved successfully.")
        query_params = f"?class_name={selected_class_name or ''}&date={selected_date.isoformat()}&term={selected_term or ''}&search={search_query}"
        return redirect(f"{reverse('mark_attendance')}{query_params}")

    selected_date_str = request.GET.get("date")
    if selected_date_str:
        selected_date = parse_date(selected_date_str) or today

    selected_class_name = request.GET.get("class_name")
    selected_term = request.GET.get("term")
    search_query = request.GET.get("search", "").strip()

    if selected_class_name:
        student_qs = student_qs.filter(current_class=selected_class_name)
    elif class_names:
        selected_class_name = class_names[0]
        student_qs = student_qs.filter(current_class=selected_class_name)

    if search_query:
        student_qs = student_qs.filter(
            Q(name__icontains=search_query) | Q(admission_number__icontains=search_query)
        )

    students = list(student_qs.order_by('name'))
    total_students = len(students)

    attendance_today = Attendance.objects.filter(school=school, date=selected_date, student__in=students)
    attendance_map = {attendance.student_id: attendance.status for attendance in attendance_today}
    status_counts = {item['status']: item['count'] for item in attendance_today.values('status').annotate(count=Count('id'))}
    present_count = status_counts.get('Present', 0)
    absent_count = status_counts.get('Absent', 0)
    late_count = status_counts.get('Late', 0)
    attendance_rate = round((present_count / total_students) * 100, 0) if total_students else 0

    summary_counts = Attendance.objects.filter(student__in=students).values('student_id', 'status').annotate(count=Count('id'))
    student_summaries = {student.id: {'present': 0, 'absent': 0, 'late': 0, 'total': 0, 'percent': 0, 'present_percent': 0, 'absent_percent': 0, 'late_percent': 0} for student in students}
    for item in summary_counts:
        student_summary = student_summaries.get(item['student_id'])
        if student_summary is None:
            continue
        student_summary[item['status'].lower()] = item['count']
        student_summary['total'] += item['count']

    for student_summary in student_summaries.values():
        total = student_summary['total']
        if total:
            student_summary['percent'] = round((student_summary['present'] / total) * 100, 0)
            student_summary['present_percent'] = round((student_summary['present'] / total) * 100, 0)
            student_summary['absent_percent'] = round((student_summary['absent'] / total) * 100, 0)
            student_summary['late_percent'] = round((student_summary['late'] / total) * 100, 0)
        else:
            student_summary['percent'] = 0
            student_summary['present_percent'] = 0
            student_summary['absent_percent'] = 0
            student_summary['late_percent'] = 0

    for student in students:
        student.attendance_status = attendance_map.get(student.id, '')
        student.attendance_summary = student_summaries.get(student.id, {'present': 0, 'absent': 0, 'late': 0, 'total': 0, 'percent': 0, 'present_percent': 0, 'absent_percent': 0, 'late_percent': 0})

    term_objects = Term.objects.filter(school=school).order_by('name')
    if term_objects.exists():
        term_options = [{'value': str(term.id), 'label': term.name} for term in term_objects]
    else:
        term_options = [
            {'value': 'First Term', 'label': 'First Term'},
            {'value': 'Second Term', 'label': 'Second Term'},
            {'value': 'Third Term', 'label': 'Third Term'},
        ]
    if not selected_term and term_options:
        selected_term = term_options[0]['value']

    return render(request, "attendance/mark_attendance.html", {
        'students': students,
        'class_names': class_names,
        'selected_class_name': selected_class_name,
        'selected_date': selected_date,
        'selected_term': selected_term,
        'term_options': term_options,
        'search_query': search_query,
        'total_students': total_students,
        'present_count': present_count,
        'absent_count': absent_count,
        'late_count': late_count,
        'attendance_rate': attendance_rate,
        'attendance_map': attendance_map,
        'student_summaries': student_summaries,
    })


def view_attendance_history(request):
    """
    View attendance history with filtering by date range, class, and student.
    """
    school = require_active_school(request)
    today = date.today()
    
    # Default date range: last 30 days
    date_from = today - timedelta(days=30)
    date_to = today
    selected_class_name = None
    selected_student_id = None
    search_query = ""
    
    # Get student queryset based on teacher access
    student_qs = Student.objects.select_related('school').filter(school=school)
    if hasattr(request.user, "teacher"):
        allowed_classes = list(get_teacher_class_names(request.user.teacher))
        student_qs = student_qs.filter(current_class__in=allowed_classes)
    
    # Get unique class names
    class_names = list(student_qs.order_by('current_class').values_list('current_class', flat=True).distinct())
    
    # Handle POST/GET filters
    if request.method == "POST" or request.GET:
        params = request.POST if request.method == "POST" else request.GET
        
        date_from_str = params.get("date_from")
        date_to_str = params.get("date_to")
        selected_class_name = params.get("class_name")
        selected_student_id = params.get("student_id")
        search_query = params.get("search", "").strip()
        
        if date_from_str:
            date_from = parse_date(date_from_str) or date_from
        if date_to_str:
            date_to = parse_date(date_to_str) or date_to
        
        # Ensure date_from is before date_to
        if date_from > date_to:
            date_from, date_to = date_to, date_from
    
    # Apply class filter
    if selected_class_name:
        student_qs = student_qs.filter(current_class=selected_class_name)
    elif class_names:
        selected_class_name = class_names[0]
        student_qs = student_qs.filter(current_class=selected_class_name)
    
    # Apply search filter
    if search_query:
        student_qs = student_qs.filter(
            Q(name__icontains=search_query) | Q(admission_number__icontains=search_query)
        )
    
    students = student_qs.order_by('name')
    
    # Get attendance records in the date range
    attendance_records = Attendance.objects.filter(
        school=school,
        student__in=students,
        date__gte=date_from,
        date__lte=date_to
    ).select_related('student').order_by('-date', 'student__name')
    
    # If specific student selected, filter further
    if selected_student_id:
        try:
            selected_student = Student.objects.get(id=selected_student_id, school=school)
            attendance_records = attendance_records.filter(student=selected_student)
        except Student.DoesNotExist:
            selected_student = None
    else:
        selected_student = None
    
    # Calculate statistics
    total_records = attendance_records.count()
    status_breakdown = {
        'present': attendance_records.filter(status='Present').count(),
        'absent': attendance_records.filter(status='Absent').count(),
        'late': attendance_records.filter(status='Late').count(),
    }
    
    if total_records > 0:
        status_breakdown['present_percent'] = round((status_breakdown['present'] / total_records) * 100, 1)
        status_breakdown['absent_percent'] = round((status_breakdown['absent'] / total_records) * 100, 1)
        status_breakdown['late_percent'] = round((status_breakdown['late'] / total_records) * 100, 1)
    else:
        status_breakdown['present_percent'] = 0
        status_breakdown['absent_percent'] = 0
        status_breakdown['late_percent'] = 0
    
    # Group attendance by date for calendar view
    dates_with_attendance = {}
    for record in attendance_records:
        date_key = record.date.isoformat()
        if date_key not in dates_with_attendance:
            dates_with_attendance[date_key] = {
                'date': record.date,
                'records': [],
                'total': 0,
                'present': 0,
                'absent': 0,
                'late': 0,
            }
        dates_with_attendance[date_key]['records'].append(record)
        dates_with_attendance[date_key]['total'] += 1
        if record.status == 'Present':
            dates_with_attendance[date_key]['present'] += 1
        elif record.status == 'Absent':
            dates_with_attendance[date_key]['absent'] += 1
        elif record.status == 'Late':
            dates_with_attendance[date_key]['late'] += 1
    
    # Sort by date (most recent first)
    dates_with_attendance = dict(sorted(dates_with_attendance.items(), reverse=True))
    
    context = {
        'attendance_records': attendance_records,
        'dates_with_attendance': dates_with_attendance,
        'class_names': class_names,
        'students': students,
        'selected_class_name': selected_class_name,
        'selected_student': selected_student,
        'selected_student_id': selected_student_id,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'total_records': total_records,
        'status_breakdown': status_breakdown,
    }
    
    return render(request, "attendance/view_history.html", context)


