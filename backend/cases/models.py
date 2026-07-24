from django.db import models


class Case(models.Model):
    ct_id = models.BigAutoField(primary_key=True)

    ct_file = models.FileField(upload_to="ct_files/")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CT {self.ct_id}"
        