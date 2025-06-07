from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project, Category, ProjectMetric, AggregateMetric
from .serializers import (
    ProjectMetricSerializer, 
    AggregateMetricSerializer,
    AggregateMetricDetailSerializer
)


class ProjectMetricViewSet(viewsets.ModelViewSet):
    queryset = ProjectMetric.objects.all()
    serializer_class = ProjectMetricSerializer

    def get_queryset(self):
        queryset = ProjectMetric.objects.all()

        # Filter by project if provided
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # Filter by category if provided
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by name if provided
        metric_name = self.request.query_params.get('name')
        if metric_name:
            queryset = queryset.filter(name=metric_name)

        return queryset

class AggregateMetricViewSet(viewsets.ModelViewSet):
    queryset = AggregateMetric.objects.all()

    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return AggregateMetricDetailSerializer
        return AggregateMetricSerializer

    @action(detail=True, methods=['post'])
    def add_project_metric(self, request, pk=None):
        aggregate_metric = self.get_object()
        metric_id = request.data.get('metric_id')

        if not metric_id:
            return Response({"error": "metric_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project_metric = ProjectMetric.objects.get(id=metric_id)
            aggregate_metric.project_metrics.add(project_metric)
            return Response({"status": "Project metric added successfully"})
        except ProjectMetric.DoesNotExist:
            return Response({"error": "Project metric not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def remove_project_metric(self, request, pk=None):
        aggregate_metric = self.get_object()
        metric_id = request.data.get('metric_id')

        if not metric_id:
            return Response({"error": "metric_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            project_metric = ProjectMetric.objects.get(id=metric_id)
            aggregate_metric.project_metrics.remove(project_metric)
            return Response({"status": "Project metric removed successfully"})
        except ProjectMetric.DoesNotExist:
            return Response({"error": "Project metric not found"}, status=status.HTTP_404_NOT_FOUND)



