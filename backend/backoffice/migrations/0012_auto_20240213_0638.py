# Generated by Django 3.2.23 on 2024-02-13 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0011_auto_20240212_1206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shipment',
            name='delivery_date',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='discharged_date',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='empty_date',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='ingate_date',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='last_free_day',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='outgate_date',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='pickup_time',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='return_day',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='return_time',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='vessel_eta',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
