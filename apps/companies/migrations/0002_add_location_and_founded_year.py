# Generated manually to add missing fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='location',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='company',
            name='founded_year',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
