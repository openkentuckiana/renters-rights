# Generated by Django 3.2.4 on 2021-06-15 22:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("rules", "0002_auto_20210615_2249")]

    operations = [
        migrations.AlterField(
            model_name="rule",
            name="ordinance",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="rules.ordinance"),
        ),
        migrations.AlterField(
            model_name="rule",
            name="rule_group",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="rules.rulegroup"),
        ),
    ]
