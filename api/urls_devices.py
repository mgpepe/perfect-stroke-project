from django.urls import path

from . import views_devices

urlpatterns = [
    path('', views_devices.device_list, name='list'),
    path('new/', views_devices.device_new, name='new'),
    path('<str:device_id>/', views_devices.device_detail, name='detail'),
]
