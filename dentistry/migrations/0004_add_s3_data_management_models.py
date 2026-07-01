# Generated migration for Dentistry S3 Data Management models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dentistry', '0003_add_cancer_detection_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='DentistryInstitution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('type', models.CharField(choices=[('dental_clinic', 'Dental Clinic'), ('orthodontic_clinic', 'Orthodontic Clinic'), ('oral_surgery_center', 'Oral Surgery Center'), ('dental_hospital', 'Dental Hospital'), ('pediatric_dental_clinic', 'Pediatric Dental Clinic'), ('cosmetic_dental_center', 'Cosmetic Dental Center')], default='dental_clinic', max_length=30)),
                ('address', models.TextField()),
                ('phone', models.CharField(max_length=20)),
                ('email', models.EmailField(max_length=254)),
                ('license_number', models.CharField(max_length=50, unique=True)),
                ('specializations', models.JSONField(blank=True, default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'dentistry_institutions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DentistryPatient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('date_of_birth', models.DateField()),
                ('gender', models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not_to_say', 'Prefer not to say')], max_length=20)),
                ('phone', models.CharField(max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('insurance_provider', models.CharField(blank=True, max_length=100)),
                ('insurance_number', models.CharField(blank=True, max_length=50)),
                ('emergency_contact_name', models.CharField(blank=True, max_length=100)),
                ('emergency_contact_phone', models.CharField(blank=True, max_length=20)),
                ('medical_history', models.TextField(blank=True)),
                ('dental_history', models.TextField(blank=True)),
                ('chief_complaint', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patients', to='dentistry.dentistryinstitution')),
            ],
            options={
                'db_table': 'dentistry_s3_patients',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DentistryFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('file_type', models.CharField(choices=[('xrays', 'X-Rays'), ('photos', 'Clinical Photos'), ('impressions', 'Digital Impressions'), ('treatment_plans', 'Treatment Plans'), ('reports', 'Reports'), ('consent_forms', 'Consent Forms'), ('general', 'General')], default='general', max_length=20)),
                ('s3_key', models.CharField(max_length=500, unique=True)),
                ('s3_url', models.URLField(max_length=500)),
                ('size', models.BigIntegerField(default=0)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('institution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='dentistry.dentistryinstitution')),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='dentistry.dentistrypatient')),
            ],
            options={
                'db_table': 'dentistry_s3_files',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DentistryAnalysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('analysis_type', models.CharField(choices=[('caries_detection', 'Caries Detection'), ('orthodontic_analysis', 'Orthodontic Analysis'), ('periodontal_assessment', 'Periodontal Assessment'), ('oral_pathology', 'Oral Pathology Detection'), ('bite_analysis', 'Bite Analysis')], max_length=30)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('confidence_score', models.FloatField(blank=True, null=True)),
                ('results', models.JSONField(blank=True, default=dict)),
                ('error_message', models.TextField(blank=True)),
                ('processing_time', models.DurationField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analyses', to='dentistry.dentistryfile')),
            ],
            options={
                'db_table': 'dentistry_s3_analyses',
                'ordering': ['-created_at'],
            },
        ),
    ]
