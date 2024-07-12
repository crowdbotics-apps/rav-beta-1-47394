# Generated by Django 3.2.23 on 2024-01-26 11:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_alter_user_user_type'),
        ('backoffice', '0003_container'),
    ]

    operations = [
        migrations.CreateModel(
            name='Shipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery_order', models.BooleanField(default=False)),
                ('delivery_order_file', models.FileField(blank=True, null=True, upload_to='delivery_orders/')),
                ('bill_of_landing', models.BooleanField(default=False)),
                ('bill_of_landing_file', models.FileField(blank=True, null=True, upload_to='bills_of_landing/')),
                ('status', models.CharField(choices=[('CONTAINER_QUEUED', 'Queued'), ('CONTAINER_ASSIGNED', 'Assigned'), ('PICKED_UP', 'Picked Up'), ('DELIVERED', 'Delivered'), ('RETURNED_EMPTY', 'Returned Empty')], max_length=20)),
                ('return_location', models.CharField(blank=True, max_length=255, null=True)),
                ('return_time', models.DateTimeField(blank=True, null=True)),
                ('pickup_time', models.DateTimeField(blank=True, null=True)),
                ('delivery_time', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('container', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backoffice.container')),
                ('driver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.driver')),
            ],
        ),
    ]
