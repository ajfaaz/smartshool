from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("academics", "0008_school_scope_remaining_models"),
        ("teachers", "0006_teacher_user"),
    ]

    operations = [
        migrations.CreateModel(
            name="Assignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("due_date", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("school", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.school")),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="academics.subject")),
                ("teacher", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="teachers.teacher")),
            ],
        ),
    ]
