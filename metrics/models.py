from django.db import models
from django.utils import timezone


class Project(models.Model):
    """Model representing a project with metadata."""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    """Model representing categories for metrics."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class ProjectMetricMeta(models.Model):
    """Model representing metrics metadata associated with projects."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='meta')
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='meta')
    source = models.CharField(max_length=255)
    url = models.URLField(max_length=1000)
    conversion_ratio = models.FloatField()

    class Meta:
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.project.name} - {self.name}"
    
    def save(self, **kwargs):
        if self.value:
            self.value *= self.conversion_ratio # converts metric value to standard unit
            return super().save(update_fields=['value', 'timestamp'])
        return super().save(*args, **kwargs)

class ProjectMetric(models.Model):
    """Model representing metrics associated with projects."""
    meta = models.OneToOneField(ProjectMetricMeta, on_delete=models.CASCADE, primary_key=True)
    value = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['timestamp']
        get_latest_by = 'timestamp'

    def __str__(self):
        return f"{self.meta.project.name} - {self.meta.name} - Metric: {self.value}"

    def save(self, *args, **kwargs):
        if not self.value: return super().save(*args, **kwargs)
        
        self.value *= self.conversion_ratio  # converts metric value to standard unit
        prev = ProjectMetric.objects.values_list('value', flat=True).get(pk=self.pk)  # pull the existing value straight from the DB
        # wrap in a transaction so that both the save and the delta‐log happen atomically
        with transaction.atomic():
            super().save(update_fields=['value', 'timestamp'], *args, **kwargs)
            ProjectMetricDelta.objects.create(meta=self.meta, value=self.value - prev)

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

