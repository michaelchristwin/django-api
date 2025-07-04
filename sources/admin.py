import json
from urllib.request import urlopen
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist

from .utils import get_baserow_impact_data
from .models import Source


@admin.action(description='Refresh impact metrics from source')
def refresh(modeladmin, request, queryset):
    impact_data = get_baserow_impact_data()
    for json_file in impact_data['results']:
        json_url = json_file['Impact Metrics JSON'][0]['url']
        response = urlopen(json_file['Impact Metrics JSON'][0]['url'])
        data = json.loads(response.read())

        for impact in data['impact_data']:
            try: 
                source = queryset.get(name=impact['source'])
                source.refresh()
            except ObjectDoesNotExist:
                print('Did not find source - '+impact['source'])
                continue


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    actions = [refresh]

