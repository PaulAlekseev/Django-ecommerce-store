# Generated by Django 4.0.5 on 2022-07-28 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0006_remove_review_review_remove_review_title_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='review',
            name='review_commentary',
            field=models.TextField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='review',
            name='review_cons',
            field=models.TextField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='review',
            name='review_pros',
            field=models.TextField(blank=True, max_length=150, null=True),
        ),
    ]
