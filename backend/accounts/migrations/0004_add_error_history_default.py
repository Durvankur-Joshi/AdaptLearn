# In accounts/migrations/0004_add_error_history_default.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_learningsession_knowledge_level_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentprogress',
            name='error_history',
            field=models.JSONField(default=list),
        ),
    ]