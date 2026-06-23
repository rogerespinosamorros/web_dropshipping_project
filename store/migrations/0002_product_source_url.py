from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="source_url",
            field=models.URLField(blank=True, verbose_name="URL de origen"),
        ),
    ]

