# Generated by Django 3.2.23 on 2024-03-29 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0022_alter_shipment_assigned_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='shipment',
            name='driver_delivered_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shipment',
            name='warehouse_accepted_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='shipment',
            name='status',
            field=models.CharField(choices=[('Queued', 'Queued'), ('Assigned', 'Assigned'), ('Picked Up', 'Picked Up'), ('Delivered', 'Delivered'), ('Accepted', 'Accepted'), ('Returned Empty', 'Returned Empty')], max_length=20),
        ),
    ]
