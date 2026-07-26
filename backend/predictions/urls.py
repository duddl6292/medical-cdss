from django.urls import path

from .views import (
    PredictionHistoryView,
    PredictionResultView,
    PredictionStatusView,
)

urlpatterns = [
    path(
        "status/<int:ct_id>/",
        PredictionStatusView.as_view(),
        name="prediction-status",
    ),
    path(
        "result/<int:ct_id>/",
        PredictionResultView.as_view(),
        name="prediction-result",
    ),
    path(
        "history/",
        PredictionHistoryView.as_view(),
        name="prediction-history",
    ),
]