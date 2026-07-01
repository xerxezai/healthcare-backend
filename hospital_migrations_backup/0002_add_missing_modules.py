"""
Migration to add missing module permissions to AdminDashboardFeatures
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hospital', '0001_initial'),  # Adjust this to your latest migration
    ]

    operations = [
        migrations.AddField(
            model_name='admindashboardfeatures',
            name='homeopathy_module',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='admindashboardfeatures',
            name='allopathy_module',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='admindashboardfeatures',
            name='dna_sequencing_module',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='admindashboardfeatures',
            name='secureneat_module',
            field=models.BooleanField(default=False),
        ),
    ]
