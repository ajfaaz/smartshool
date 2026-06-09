from django.db import migrations, models
import django.db.models.deletion


def populate_attendance_school(apps, schema_editor):
    Attendance = apps.get_model("attendance", "Attendance")
    School = apps.get_model("core", "School")

    default_school = School.objects.first()
    if default_school is None:
        default_school = School.objects.create(
            name="Default School",
            address="Not set",
            phone="0000000000",
            email="defaultschool@example.com",
        )

    for attendance in Attendance.objects.select_related("student"):
        attendance.school = getattr(attendance.student, "school", default_school) or default_school
        attendance.save(update_fields=["school"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("students", "0005_student_school_and_simplify_fields"),
        ("attendance", "0002_alter_attendance_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="attendance",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.RunPython(populate_attendance_school, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="attendance",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
    ]
