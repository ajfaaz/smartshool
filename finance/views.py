from django.shortcuts import render, redirect
from django.db.models import Sum
from students.models import Student
from .models import Payment, FeeStructure
from core.school_scope import require_active_school, get_scoped_object


def record_payment(request):
    school = require_active_school(request)

    students = Student.objects.select_related('school').filter(school=school)

    if request.method == "POST":

        student_id = request.POST["student"]
        amount = int(request.POST["amount"])
        term = request.POST.get("term", "")
        reference = request.POST["reference"]

        student = get_scoped_object(request, Student, id=student_id)
        fee = FeeStructure.objects.filter(
            school=student.school,
            class_name=student.current_class,
            term=term
        ).first()

        if fee is None:
            fee = FeeStructure.objects.filter(
                school=student.school,
                class_name=student.current_class,
                term=term
            ).first()

        expected_fee = fee.amount if fee else 0
        previous_paid = Payment.objects.filter(
            student=student,
            term=term
        ).aggregate(total=Sum("amount_paid"))["total"] or 0
        balance = expected_fee - (previous_paid + amount)

        if balance == 0:
            status = "Paid"
        elif balance > 0:
            status = "Part Payment"
        else:
            status = "Overpaid"

        Payment.objects.create(
            student=student,
            amount_paid=amount,
            term=term,
            status=status,
            reference=reference
        )

        return redirect("record_payment")

    return render(request, "finance/record_payment.html", {"students": students})

from django.shortcuts import render
from students.models import Student

def pay_fees(request, student_id):

    student = get_scoped_object(request, Student, id=student_id)

    return render(request, 'finance/pay_fees.html', {
        'student': student
    })
