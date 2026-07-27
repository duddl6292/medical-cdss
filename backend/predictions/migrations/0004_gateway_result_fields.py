from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("predictions", "0003_predictionresult"),
    ]

    operations = [
        migrations.AddField(
            model_name="prediction",
            name="error_code",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
        migrations.AddField(
            model_name="prediction",
            name="error_message",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="predictionresult",
            name="entropy_uri",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="predictionresult",
            name="preview_uri",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="predictionresult",
            name="probability_uri",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="predictionresult",
            name="result_json_uri",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="predictionresult",
            name="uncertainty_uri",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]
