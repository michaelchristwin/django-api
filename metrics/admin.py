from django.contrib import admin
from .models import Project, Category, ProjectMetric, ProjectMetricMeta, ProjectMetricDelta, AggregateMetric

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(ProjectMetricMeta)
class ProjectMetricMetaAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'category')
    list_filter = ('project', 'category')
    search_fields = ('name', 'project__name', 'category__name')

@admin.register(ProjectMetric)
class ProjectMetricAdmin(admin.ModelAdmin):
    list_display = ('meta__name', 'value', 'timestamp')
    list_filter = ('meta__name', 'meta__category', 'timestamp')
    search_fields = ('meta__name', 'meta__project__name', 'meta__category__name')

@admin.register(ProjectMetricDelta)
class ProjectMetricDeltaAdmin(admin.ModelAdmin):
    list_display = ('meta__name', 'value', 'timestamp')
    list_filter = ('meta__name', 'meta__category', 'timestamp')
    search_fields = ('meta__name', 'meta__project__name', 'meta__category__name')

@admin.register(AggregateMetric)
class AggregateMetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'aggregation_method')
    filter_horizontal = ('project_metrics', 'categories')
    search_fields = ('name', 'description')


