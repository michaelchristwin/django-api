from django.db import models
from django.utils import timezone

CATEGORIES = ('solar', 'carbon', 'cookstove', 'biodiversity')


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


