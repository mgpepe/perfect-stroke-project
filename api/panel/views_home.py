"""Overview screen at /panel/."""

from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone

from api.models import (
    Brand, BrandModel, BrushHairType, Color, Device, File, Paint, Paper,
    PaperMaterial, PaperSurface, Pigment, Store, Stroke, Tool, ToolShape,
    ToolSize, ToolType,
)


@staff_member_required(login_url='/admin/login/')
def home(request):
    online_threshold = timezone.now() - timedelta(minutes=15)

    device_stats = {
        'total': Device.objects.count(),
        'online': Device.objects.filter(last_heartbeat_at__gte=online_threshold).count(),
        'failed': Device.objects.filter(last_status='failed').count(),
    }

    artifacts = [
        {'label': 'Strokes', 'count': Stroke.objects.count(),
         'sub': f'{Stroke.objects.exclude(image_url="").count()} with images',
         'url_name': 'panel:strokes:list'},
        {'label': 'Paints', 'count': Paint.objects.count(), 'sub': '',
         'url_name': 'panel:paints:list'},
        {'label': 'Papers', 'count': Paper.objects.count(), 'sub': '',
         'url_name': 'panel:papers:list'},
        {'label': 'Tools', 'count': Tool.objects.count(), 'sub': '',
         'url_name': 'panel:tools:list'},
    ]

    taxonomy = [
        ('Brands', Brand.objects.count(), 'brands'),
        ('Brand models', BrandModel.objects.count(), 'brand-models'),
        ('Colors', Color.objects.count(), 'colors'),
        ('Pigments', Pigment.objects.count(), 'pigments'),
        ('Stores', Store.objects.count(), 'stores'),
        ('Paper materials', PaperMaterial.objects.count(), 'paper-materials'),
        ('Paper surfaces', PaperSurface.objects.count(), 'paper-surfaces'),
        ('Tool types', ToolType.objects.count(), 'tool-types'),
        ('Tool shapes', ToolShape.objects.count(), 'tool-shapes'),
        ('Tool sizes', ToolSize.objects.count(), 'tool-sizes'),
        ('Brush hair types', BrushHairType.objects.count(), 'brush-hair-types'),
    ]

    files_total = File.objects.count()

    return render(request, 'panel/home.html', {
        'device_stats': device_stats,
        'artifacts': artifacts,
        'taxonomy': taxonomy,
        'files_total': files_total,
    })
