import json

from django.contrib import admin
from urllib.request import urlopen

from .utils import get_baserow_data
from .models import Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.action(description='Refresh impact metrics from source')
def refresh_impact_metrics(modeladmin, request, queryset):
    impact_data = get_baserow_data('171320', "filter__field_2405062__not_empty&include=Impact Metrics JSON")
    for json_file in impact_data['results']:
        json_url = json_file['Impact Metrics JSON'][0]['url']
        response = urlopen(json_file['Impact Metrics JSON'][0]['url'])
        data = json.loads(response.read())

        for impact in data['impact_data']:
            source = queryset.get(name=impact['source'])
            source.refresh()
