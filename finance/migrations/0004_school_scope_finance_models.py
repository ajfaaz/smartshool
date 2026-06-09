from django.db import migrations, models
import django.db.models.deletion


def populate_school_scoped_finance(apps, schema_editor):
    School = apps.get_model("core", "School")
    FeeStructure = apps.get_model("finance", "FeeStructure")
    Payment = apps.get_model("finance", "Payment")
    FeePayment = apps.get_model("finance", "FeePayment")

    default_school = School.objects.first()
    if default_school is None:
        default_school = School.objects.create(
            name="Default School",
            address="Not set",
            phone="0000000000",
            email="defaultschool@example.com",
        )

    for fee in FeeStructure.objects.all():
        fee.school = default_school
        fee.save(update_fields=["school"])

    for payment in Payment.objects.select_related("student"):
        payment.school = getattr(payment.student, "school", default_school) or default_school
        payment.save(update_fields=["school"])

    for fee_payment in FeePayment.objects.select_related("student"):
        fee_payment.school = getattr(fee_payment.student, "school", default_school) or default_school
        fee_payment.save(update_fields=["school"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("students", "0005_student_school_and_simplify_fields"),
        ("finance", "0003_feepayment"),
    ]

    operations = [
        migrations.AddField(
            model_name="feepayment",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AddField(
            model_name="feestructure",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.RunPython(populate_school_scoped_finance, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="feepayment",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="feestructure",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
    ]
