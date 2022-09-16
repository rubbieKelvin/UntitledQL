from django.db import migrations


def lowercase_role(apps, schema_editor):
    User = apps.get_model("main", "User")
    for row in User.objects.all():
        row.role = row.role.lower()
        row.save(update_fields=["role"])


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0003_alter_user_role"),
    ]

    operations = [
        migrations.RunPython(lowercase_role),
    ]
