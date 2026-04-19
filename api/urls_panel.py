from django.urls import path, include

from . import views_panel

devices_urls = ([
    path('', views_panel.device_list, name='list'),
    path('new/', views_panel.device_new, name='new'),
    path('<str:device_id>/', views_panel.device_detail, name='detail'),
], 'devices')

urlpatterns = [
    path('', views_panel.home, name='home'),
    path('devices/', include(devices_urls, namespace='devices')),
]
