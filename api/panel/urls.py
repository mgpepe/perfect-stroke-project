from django.urls import include, path

from . import (
    views_device, views_generic, views_home, views_paint, views_paper,
    views_stroke, views_tool,
)
from .registry import LOOKUPS


devices_urls = ([
    path('', views_device.device_list, name='list'),
    path('new/', views_device.device_new, name='new'),
    path('<str:device_id>/', views_device.device_detail, name='detail'),
], 'devices')

strokes_urls = ([
    path('', views_stroke.stroke_list, name='list'),
    path('new/', views_stroke.stroke_new, name='new'),
    path('<str:pk>/', views_stroke.stroke_detail, name='detail'),
    path('<str:pk>/delete/', views_stroke.stroke_delete, name='delete'),
], 'strokes')

paints_urls = ([
    path('', views_paint.paint_list, name='list'),
    path('new/', views_paint.paint_new, name='new'),
    path('<str:pk>/', views_paint.paint_detail, name='detail'),
    path('<str:pk>/delete/', views_paint.paint_delete, name='delete'),
], 'paints')

papers_urls = ([
    path('', views_paper.paper_list, name='list'),
    path('new/', views_paper.paper_new, name='new'),
    path('<str:pk>/', views_paper.paper_detail, name='detail'),
    path('<str:pk>/delete/', views_paper.paper_delete, name='delete'),
], 'papers')

tools_urls = ([
    path('', views_tool.tool_list, name='list'),
    path('new/', views_tool.tool_new, name='new'),
    path('<str:pk>/', views_tool.tool_detail, name='detail'),
    path('<str:pk>/delete/', views_tool.tool_delete, name='delete'),
], 'tools')


def _generic_urls(slug):
    return ([
        path('', views_generic.generic_list, {'slug': slug}, name='list'),
        path('new/', views_generic.generic_new, {'slug': slug}, name='new'),
        path('<str:pk>/', views_generic.generic_detail, {'slug': slug}, name='detail'),
        path('<str:pk>/delete/', views_generic.generic_delete, {'slug': slug}, name='delete'),
    ], slug)


generic_patterns = [
    path(f'{panel.slug}/', include(_generic_urls(panel.slug), namespace=panel.slug))
    for panel in LOOKUPS
]


urlpatterns = [
    path('', views_home.home, name='home'),
    path('devices/', include(devices_urls, namespace='devices')),
    path('strokes/', include(strokes_urls, namespace='strokes')),
    path('paints/', include(paints_urls, namespace='paints')),
    path('papers/', include(papers_urls, namespace='papers')),
    path('tools/', include(tools_urls, namespace='tools')),
    path('', include((generic_patterns, 'generic'), namespace='generic')),
]
