from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_teacher_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentbatch',
            name='parent_batch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sub_batches', to='api.studentbatch'),
        ),
    ]

