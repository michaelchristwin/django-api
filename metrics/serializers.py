# serializers.py
from rest_framework import serializers
from .models import ProjectMetric, ProjectMetricMeta, ProjectMetricDelta, AggregateMetric

from projects.serializers import ProjectSerializer, CategorySerializer
from projects.models import Project, Category

class ProjectMetricMetaSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.all(), 
        source='project', 
        write_only=True
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        source='category', 
        write_only=True,
        required=False
    )

    class Meta:
        model = ProjectMetricMeta
        fields = ['id', 'name', 'project', 'project_id', 'category', 'category_id']

class ProjectMetricSerializer(serializers.ModelSerializer):
    meta = ProjectMetricMetaSerializer(read_only=True)

    class Meta:
        model = ProjectMetric
        fields = ['meta', 'value', 'timestamp']

class ProjectMetricDeltaSerializer(serializers.ModelSerializer):
    meta = ProjectMetricMetaSerializer(read_only=True)

    class Meta:
        model = ProjectMetricDelta
        fields = ['meta', 'value', 'timestamp']

class AggregateMetricSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    category_ids = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='categories',
        write_only=True,
        many=True,
        required=False
    )

    class Meta:
        model = AggregateMetric
        fields = ['id', 'name', 'description', 'aggregation_method', 'categories', 'category_ids']


class AggregateMetricDetailSerializer(serializers.ModelSerializer):
    aggregated_value = serializers.SerializerMethodField()
    contributing_projects = serializers.SerializerMethodField()
    
    class Meta:
        model = AggregateMetric
        fields = ['id', 'name', 'description', 'aggregation_method', 'aggregated_value', 'contributing_projects']
    
    def get_aggregated_value(self, obj):
        return obj.get_aggregated_value()
    
    def get_contributing_projects(self, obj):
        projects = obj.get_contributing_projects()
        return [{'id': p.id, 'name': p.name, 'logo_url': p.logo_url} for p in projects]


