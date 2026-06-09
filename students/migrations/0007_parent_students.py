from django.db import migrations, models


def populate_parent_students(apps, schema_editor):
    Parent = apps.get_model("students", "Parent")

    for parent in Parent.objects.exclude(student_id=None):
        parent.students.add(parent.student_id)


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0006_parent_school"),
    ]

    operations = [
        migrations.AddField(
            model_name="parent",
            name="students",
            field=models.ManyToManyField(blank=True, related_name="parents", to="students.student"),
        ),
        migrations.AlterField(
            model_name="parent",
            name="student",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to="students.student"),
        ),
        migrations.RunPython(populate_parent_students, migrations.RunPython.noop),
    ]
