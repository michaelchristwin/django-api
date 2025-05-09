from django.contrib import admin
from .models import Project, Category, ProjectMetric, AggregateMetric

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')

@admin.register(ProjectMetric)
class ProjectMetricAdmin(admin.ModelAdmin):
    list_display = ('project', 'name', 'value', 'category', 'timestamp')
    list_filter = ('project', 'category', 'timestamp')
    search_fields = ('name', 'project__name', 'category__name')

@admin.register(AggregateMetric)
class AggregateMetricAdmin(admin.ModelAdmin):
    list_display = ('name', 'aggregation_method')
    filter_horizontal = ('project_metrics', 'categories')
    search_fields = ('name', 'description')


