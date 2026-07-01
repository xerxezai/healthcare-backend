from django.db import migrations, models

def set_default_full_name(apps, schema_editor):
    CustomUser = apps.get_model('hospital', 'CustomUser')
    for user in CustomUser.objects.all():
        user.full_name = user.email.split('@')[0]
        user.save()

class Migration(migrations.Migration):
    dependencies = [
        ('hospital', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='full_name',
            field=models.CharField(max_length=255, default=''),
            preserve_default=False,
        ),
        migrations.RunPython(set_default_full_name),
    ]
