from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'brands', views.BrandViewSet)
router.register(r'brand-models', views.BrandModelViewSet)
router.register(r'colors', views.ColorViewSet)
router.register(r'stores', views.StoreViewSet)
router.register(r'paper-materials', views.PaperMaterialViewSet)
router.register(r'paper-surfaces', views.PaperSurfaceViewSet)
router.register(r'tool-types', views.ToolTypeViewSet)
router.register(r'tool-shapes', views.ToolShapeViewSet)
router.register(r'tool-sizes', views.ToolSizeViewSet)
router.register(r'brush-hair-types', views.BrushHairTypeViewSet)
router.register(r'pigments', views.PigmentViewSet)
router.register(r'files', views.FileViewSet)
router.register(r'stroke-images', views.StrokeImageViewSet, basename='stroke-images')
router.register(r'paints', views.PaintViewSet)
router.register(r'papers', views.PaperViewSet)
router.register(r'tools', views.ToolViewSet)
router.register(r'strokes', views.StrokeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('devices/<str:device_id>/config/', views.device_config, name='device-config'),
    path('devices/<str:device_id>/heartbeat/', views.device_heartbeat, name='device-heartbeat'),
    path('devices/<str:device_id>/wifi/', views.device_wifi, name='device-wifi'),
]
