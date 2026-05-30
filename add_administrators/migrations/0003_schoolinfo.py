from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('add_administrators', '0002_rename_client_id_administratorprofile_institution_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='SchoolInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('institution_id', models.CharField(max_length=50, unique=True)),
                ('school_name', models.CharField(max_length=255)),
                ('address', models.TextField()),
                ('place', models.CharField(max_length=200)),
                ('pincode', models.CharField(max_length=10)),
                ('phone', models.CharField(max_length=15)),
                ('email', models.EmailField(max_length=254)),
                ('logo_url', models.URLField(blank=True, max_length=500, null=True)),
                ('logo_public_id', models.CharField(blank=True, max_length=255, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
