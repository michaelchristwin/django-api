from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, CategoryViewSet, ProjectMetricViewSet, AggregateMetricViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'project-metrics', ProjectMetricViewSet)
router.register(r'aggregate-metrics', AggregateMetricViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
