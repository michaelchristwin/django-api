from django.db import models
from django.utils import timezone

CATEGORIES = {
    "grants": "Grants to Impact Projects",
    "investments": "Investments in Impact Projects",
    "waste": "Waste Collected",
    "wasteX": "Waste Collection Action",
    "bridged-cred": "Ecological Credits Bridged",
    "retired-cred": "Onchain credits retired",
    "issued-cred": "Onchain Credits Issued",
    "borrowers": "Borrowers",
    "renewable": "Energy Generated",
    "ubi": "UBI distributed",
}


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

    name = models.CharField(max_length=255, choices=CATEGORIES, primary_key=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"
