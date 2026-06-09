from django.contrib.auth.hashers import make_password
from django.db import migrations, models
import django.db.models.deletion


def populate_teacher_users(apps, schema_editor):
    Teacher = apps.get_model("teachers", "Teacher")
    User = apps.get_model("auth", "User")

    for teacher in Teacher.objects.all():
        if getattr(teacher, "user_id", None):
            continue

        base_username = "".join((teacher.name or "teacher").lower().split()) or "teacher"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user = User.objects.create(
            username=username,
            password=make_password("teacher123"),
            first_name=(teacher.name or "").split(" ", 1)[0],
            last_name=(teacher.name or "").split(" ", 1)[1] if " " in (teacher.name or "") else "",
        )
        teacher.user = user
        teacher.save(update_fields=["user"])


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("teachers", "0005_teachersubject_school"),
    ]

    operations = [
        migrations.AddField(
            model_name="teacher",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="auth.user",
            ),
        ),
        migrations.RunPython(populate_teacher_users, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="teacher",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to="auth.user",
            ),
        ),
    ]
