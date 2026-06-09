from django.db import migrations, models
import django.db.models.deletion


def populate_class_school(apps, schema_editor):
    Class = apps.get_model("academics", "Class")
    School = apps.get_model("core", "School")

    default_school = School.objects.first()
    if default_school is None:
        default_school = School.objects.create(
            name="Default School",
            address="Not set",
            phone="0000000000",
            email="defaultschool@example.com",
        )

    for school_class in Class.objects.all():
        school_class.school = default_school
        school_class.save(update_fields=["school"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("academics", "0006_result_total"),
    ]

    operations = [
        migrations.AddField(
            model_name="class",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.RunPython(populate_class_school, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="class",
            name="section",
        ),
        migrations.AlterField(
            model_name="class",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
    ]
