from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('id_card', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='idcardform',
            name='photo_url',
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='idcardform',
            name='photo_key',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
