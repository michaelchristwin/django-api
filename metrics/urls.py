from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectMetricViewSet, AggregateMetricViewSet

router = DefaultRouter()
router.register(r'project-metrics', ProjectMetricViewSet)
router.register(r'aggregate-metrics', AggregateMetricViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
