from django.db import migrations, models
import django.db.models.deletion


def populate_teacher_subject_school(apps, schema_editor):
    TeacherSubject = apps.get_model("teachers", "TeacherSubject")
    School = apps.get_model("core", "School")

    default_school = School.objects.first()
    if default_school is None:
        default_school = School.objects.create(
            name="Default School",
            address="Not set",
            phone="0000000000",
            email="defaultschool@example.com",
        )

    for assignment in TeacherSubject.objects.select_related("teacher"):
        assignment.school = getattr(assignment.teacher, "school", default_school) or default_school
        assignment.save(update_fields=["school"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("teachers", "0004_teacher_school_and_simplify_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="teachersubject",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.RunPython(populate_teacher_subject_school, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="teachersubject",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
    ]
