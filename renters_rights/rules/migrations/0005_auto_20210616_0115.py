# Generated by Django 3.2.4 on 2021-06-16 01:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("rules", "0004_auto_20210616_0106")]

    operations = [
        migrations.RemoveField(model_name="rule", name="url"),
        migrations.AddField(
            model_name="ordinance", name="url", field=models.URLField(default="http://example.com"), preserve_default=False
        ),
        migrations.RemoveField(model_name="rule", name="ordinance"),
        migrations.AddField(model_name="rule", name="ordinance", field=models.ManyToManyField(to="rules.Ordinance")),
    ]