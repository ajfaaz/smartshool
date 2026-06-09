from django.db import migrations, models
import django.db.models.deletion


def populate_student_fields(apps, schema_editor):
    Student = apps.get_model("students", "Student")
    School = apps.get_model("core", "School")

    default_school = School.objects.first()
    if default_school is None:
        default_school = School.objects.create(
            name="Default School",
            address="Not set",
            phone="0000000000",
            email="defaultschool@example.com",
        )

    for student in Student.objects.all():
        full_name = (student.name or "").strip()
        if not full_name:
            first_name = (getattr(student, "first_name", "") or "").strip()
            last_name = (getattr(student, "last_name", "") or "").strip()
            full_name = f"{first_name} {last_name}".strip()

        current_class_name = ""
        current_class = getattr(student, "current_class", None)
        student_class = getattr(student, "student_class", None)
        if current_class:
            current_class_name = str(current_class)
        elif student_class:
            current_class_name = str(student_class)

        student.name = full_name or student.admission_number
        student.current_class_name = current_class_name
        student.school = default_school
        student.save(update_fields=["name", "current_class_name", "school"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("students", "0004_student_current_class_student_name_student_session"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AddField(
            model_name="student",
            name="current_class_name",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AlterField(
            model_name="student",
            name="admission_number",
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name="student",
            name="parent_phone",
            field=models.CharField(max_length=20),
        ),
        migrations.RunPython(populate_student_fields, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="student",
            name="current_class",
        ),
        migrations.RemoveField(
            model_name="student",
            name="student_class",
        ),
        migrations.RemoveField(
            model_name="student",
            name="user",
        ),
        migrations.RemoveField(
            model_name="student",
            name="first_name",
        ),
        migrations.RemoveField(
            model_name="student",
            name="gender",
        ),
        migrations.RemoveField(
            model_name="student",
            name="last_name",
        ),
        migrations.RemoveField(
            model_name="student",
            name="session",
        ),
        migrations.RenameField(
            model_name="student",
            old_name="current_class_name",
            new_name="current_class",
        ),
        migrations.AlterField(
            model_name="student",
            name="current_class",
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name="student",
            name="name",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="student",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
    ]
