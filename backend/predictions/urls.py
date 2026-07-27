from django.urls import path

from .views import (
    PredictionArtifactView,
    PredictionHistoryView,
    PredictionResultView,
    PredictionStartView,
    PredictionStatusView,
)

urlpatterns = [
    path(
        "cases/<int:ct_id>/predictions/",
        PredictionStartView.as_view(),
        name="prediction-start",
    ),
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
        "result/<int:ct_id>/artifacts/<str:artifact>/",
        PredictionArtifactView.as_view(),
        name="prediction-artifact",
    ),
    path(
        "history/",
        PredictionHistoryView.as_view(),
        name="prediction-history",
    ),
]
