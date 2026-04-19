"""Panel UI for managing a device's known WiFi networks."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from api.models import Device, WifiNetwork


@staff_member_required(login_url='/admin/login/')
def wifi_list(request, device_id):
    device = get_object_or_404(Device, id=device_id)

    if request.method == 'POST':
        ssid = (request.POST.get('ssid') or '').strip()[:64]
        password = (request.POST.get('password') or '')[:128]
        try:
            priority = int(request.POST.get('priority') or 50)
        except ValueError:
            priority = 50
        country = (request.POST.get('country') or device.wifi_networks.first().country
                   if device.wifi_networks.exists() else 'BG').strip().upper()[:2] or 'BG'
        notes = (request.POST.get('notes') or '').strip()[:255]
        if not ssid:
            messages.error(request, 'SSID is required.')
        else:
            obj, created = WifiNetwork.objects.update_or_create(
                device=device, ssid=ssid,
                defaults={
                    'password': password,
                    'priority': priority,
                    'country': country,
                    'notes': notes,
                },
            )
            messages.success(
                request,
                f'Added {ssid!r}.' if created else f'Updated {ssid!r}.',
            )
        return redirect('panel:devices:wifi_list', device_id=device.id)

    return render(request, 'panel/devices/wifi_list.html', {
        'device': device,
        'networks': device.wifi_networks.all(),
    })


@staff_member_required(login_url='/admin/login/')
def wifi_delete(request, device_id, network_id):
    device = get_object_or_404(Device, id=device_id)
    network = get_object_or_404(WifiNetwork, id=network_id, device=device)
    if request.method == 'POST':
        ssid = network.ssid
        network.delete()
        messages.success(request, f'Removed {ssid!r}.')
        return redirect('panel:devices:wifi_list', device_id=device.id)
    return render(request, 'panel/devices/wifi_delete.html', {
        'device': device, 'network': network,
    })
