from django.urls import path

from .views import PredictView

urlpatterns = [
    path("cases/", PredictView.as_view(), name="case-create"),
    # Backward-compatible alias retained for the restored local backup.
    path("predict/", PredictView.as_view(), name="predict"),
]
