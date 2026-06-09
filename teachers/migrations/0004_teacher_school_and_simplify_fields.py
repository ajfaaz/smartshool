from django.db import migrations, models
import django.db.models.deletion


def populate_teacher_fields(apps, schema_editor):
    Teacher = apps.get_model("teachers", "Teacher")
    School = apps.get_model("core", "School")

    default_school = School.objects.first()
    if default_school is None:
        default_school = School.objects.create(
            name="Default School",
            address="Not set",
            phone="0000000000",
            email="defaultschool@example.com",
        )

    for teacher in Teacher.objects.all():
        first_name = (getattr(teacher, "first_name", "") or "").strip()
        last_name = (getattr(teacher, "last_name", "") or "").strip()
        teacher.name = f"{first_name} {last_name}".strip() or "Unnamed Teacher"
        teacher.subject_name = "General"
        teacher.school = default_school
        teacher.save(update_fields=["name", "subject_name", "school"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("teachers", "0003_teachersubject"),
    ]

    operations = [
        migrations.AddField(
            model_name="teacher",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AddField(
            model_name="teacher",
            name="name",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="teacher",
            name="subject_name",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.RunPython(populate_teacher_fields, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="teacher",
            name="email",
        ),
        migrations.RemoveField(
            model_name="teacher",
            name="first_name",
        ),
        migrations.RemoveField(
            model_name="teacher",
            name="gender",
        ),
        migrations.RemoveField(
            model_name="teacher",
            name="last_name",
        ),
        migrations.RenameField(
            model_name="teacher",
            old_name="subject_name",
            new_name="subject",
        ),
        migrations.AlterField(
            model_name="teacher",
            name="name",
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name="teacher",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="teacher",
            name="subject",
            field=models.CharField(max_length=100),
        ),
    ]
