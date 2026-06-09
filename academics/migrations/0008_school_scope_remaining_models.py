from django.db import migrations, models
import django.db.models.deletion


def populate_school_scoped_academics(apps, schema_editor):
    School = apps.get_model("core", "School")
    Session = apps.get_model("academics", "Session")
    Term = apps.get_model("academics", "Term")
    Subject = apps.get_model("academics", "Subject")
    Result = apps.get_model("academics", "Result")

    default_school = School.objects.first()
    if default_school is None:
        default_school = School.objects.create(
            name="Default School",
            address="Not set",
            phone="0000000000",
            email="defaultschool@example.com",
        )

    for session in Session.objects.all():
        session.school = default_school
        session.save(update_fields=["school"])

    for term in Term.objects.all():
        term.school = default_school
        term.save(update_fields=["school"])

    for subject in Subject.objects.all():
        subject.school = default_school
        subject.save(update_fields=["school"])

    for result in Result.objects.select_related("student"):
        result.school = getattr(result.student, "school", default_school) or default_school
        result.save(update_fields=["school"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("students", "0005_student_school_and_simplify_fields"),
        ("academics", "0007_class_school_and_remove_section"),
    ]

    operations = [
        migrations.AddField(
            model_name="result",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AddField(
            model_name="session",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AddField(
            model_name="subject",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AddField(
            model_name="term",
            name="school",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.RunPython(populate_school_scoped_academics, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="result",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="session",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="subject",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
        migrations.AlterField(
            model_name="term",
            name="school",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="core.school",
            ),
        ),
    ]
