from django.db import migrations, models
import django.db.models.deletion


def populate_parent_school(apps, schema_editor):
    Parent = apps.get_model("students", "Parent")
    School = apps.get_model("core", "School")

    default_school = School.objects.first()
    if default_school is None:
        default_school = School.objects.create(
            name="Default School",
            address="Not set",
            phone="0000000000",
            email="defaultschool@example.com",
        )

    for parent in Parent.objects.select_related("student"):
        parent.school = getattr(parent.student, "school", default_school) or default_school
        parent.save(update_fields=["school"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("students", "0005_student_school_and_simplify_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="parent",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.RunPython(populate_parent_school, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="parent",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
    ]
