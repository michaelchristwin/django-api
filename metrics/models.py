from django.utils import timezone
from django.db import models, transaction

from projects.models import Project, Category

SOURCES = {'client': 'Project supplied', 'dune': 'Dune API', 'graphql': 'Subghraph index', 'near': 'Near blockchain', 'regen': 'Regen blockchain'}


class ProjectMetricMeta(models.Model):
    """Model representing metrics metadata associated with projects."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='meta')
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='meta')
    source = models.CharField(max_length=255, default=SOURCES['client'], choices=SOURCES)
    url = models.URLField(max_length=1000)
    query = models.CharField(max_length=1000)
    json_key = models.CharField(max_length=1000)
    conversion_ratio = models.FloatField()

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.project.name} - {self.name}"


class ProjectMetric(models.Model):
    """Model representing metrics associated with projects."""
    meta = models.OneToOneField(ProjectMetricMeta, on_delete=models.CASCADE)
    db_id = models.IntegerField(primary_key=True)
    value = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['timestamp']
        get_latest_by = 'timestamp'

    def __str__(self):
        return f"{self.meta.project.name} - {self.meta.name} - Metric: {self.value}"

    def save(self, *args, **kwargs):
        # Check if this instance already exists in the DB
        if not self._state.adding:
            old = ProjectMetric.objects.only("value").get(pk=self.pk)
            if old.value != self.value:
                with transaction.atomic():
                    ProjectMetricDelta.objects.create(meta=self.meta, value=self.value - old.value, timestamp=self.timestamp)
                    self.timestamp = timezone.now()
                    return super().save(update_fields=["value", "timestamp"], *args, **kwargs)
        return super().save(*args, **kwargs)


class ProjectMetricDelta(models.Model):
    """Model representing metrics delta associated with projects."""
    meta = models.ForeignKey(ProjectMetricMeta, on_delete=models.CASCADE, related_name='deltas')
    value = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['timestamp']

    def __str__(self):
        return f"{self.metric.meta.project.name} - {self.name} - Delta: {self.value}"


class AggregateMetric(models.Model):
    """Model representing aggregate metrics across multiple projects."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    project_metrics = models.ManyToManyField(ProjectMetric, related_name='aggregate_metrics')

    # Optional category filter
    categories = models.ManyToManyField(Category, blank=True, related_name='aggregate_metrics')

    # Aggregation method choices
    AGGREGATION_CHOICES = [
        ('SUM', 'Sum'),
        ('AVG', 'Average'),
        ('MIN', 'Minimum'),
        ('MAX', 'Maximum'),
        ('COUNT', 'Count'),
    ]
    aggregation_method = models.CharField(max_length=10, choices=AGGREGATION_CHOICES, default='SUM')

    def __str__(self):
        return self.name

    def get_aggregated_value(self):
        """Calculate the aggregated value based on the specified method."""
        metrics = self.project_metrics.all()
        
        # Apply category filter if categories are specified
        if self.categories.exists():
            category_ids = self.categories.values_list('id', flat=True)
            metrics = metrics.filter(category_id__in=category_ids)
        
        if not metrics.exists():
            return 0
        
        values = [metric.value for metric in metrics]
        
        if self.aggregation_method == 'SUM':
            return sum(values)
        elif self.aggregation_method == 'AVG':
            return sum(values) / len(values)
        elif self.aggregation_method == 'MIN':
            return min(values)
        elif self.aggregation_method == 'MAX':
            return max(values)
        elif self.aggregation_method == 'COUNT':
            return len(values)
        
        return 0    
    
    def get_contributing_projects(self):
        """Get all projects that contribute to this aggregate metric."""
        project_ids = self.project_metrics.values_list('project_id', flat=True).distinct()
        return Project.objects.filter(id__in=project_ids)

