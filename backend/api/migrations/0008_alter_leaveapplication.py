# Generated manually - alter LeaveApplication to use date field instead of day+slot_index

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_alter_department_id_alter_generatedtimetable_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='leaveapplication',
            name='day',
        ),
        migrations.RemoveField(
            model_name='leaveapplication',
            name='slot_index',
        ),
        migrations.AddField(
            model_name='leaveapplication',
            name='date',
            field=models.DateField(default='2026-03-09'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='leaveapplication',
            name='admin_remarks',
            field=models.TextField(blank=True, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='leaveapplication',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

