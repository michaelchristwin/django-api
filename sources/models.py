from django.db import models
from django.utils import timezone

from . import utils

SOURCES = {'client': 'Project supplied', 'dune': 'Dune API', 'graphql': 'Subghraph index', 'near': 'Near blockchain', 'regen': 'Regen blockchain'}


class Source(models.Model):
    """Model representing project impact metrics sources"""
    name = models.CharField(max_length=255, choices=SOURCES, primary_key=True)

    def __str__(self):
        return f"Impact metric source - {self.name}"

    def refresh(self):
        func = getattr(utils, 'refresh_' + self.name)
        return func()  # Call the function


