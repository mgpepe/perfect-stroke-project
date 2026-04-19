"""Custom admin panel at /panel/.

Progressively replaces the stock Django admin. Devices is the first module;
Strokes, Paints, Papers, Tools will migrate here later. Staff-only, reusing
/admin/login/ for auth.
"""

from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Device, Stroke, Paint, Paper


@staff_member_required(login_url='/admin/login/')
def home(request):
    online_threshold = timezone.now() - timedelta(minutes=15)
    stats = {
        'devices_total': Device.objects.count(),
        'devices_online': Device.objects.filter(last_heartbeat_at__gte=online_threshold).count(),
        'devices_failed': Device.objects.filter(last_status='failed').count(),
        'strokes_total': Stroke.objects.count(),
        'strokes_with_images': Stroke.objects.exclude(image_url='').count(),
        'paints_total': Paint.objects.count(),
        'papers_total': Paper.objects.count(),
    }
    return render(request, 'panel/home.html', {'stats': stats})


# ─── Devices ─────────────────────────────────────────────────────

@staff_member_required(login_url='/admin/login/')
def device_list(request):
    devices = Device.objects.all().order_by('id')
    return render(request, 'panel/devices/list.html', {'devices': devices})


@staff_member_required(login_url='/admin/login/')
def device_detail(request, device_id):
    device = get_object_or_404(Device, id=device_id)
    if request.method == 'POST':
        device.name = (request.POST.get('name') or '').strip()[:128]
        device.desired_git_ref = (request.POST.get('desired_git_ref') or 'main').strip()[:64]
        device.save(update_fields=['name', 'desired_git_ref', 'updated_at'])
        messages.success(request, 'Device updated.')
        return redirect('panel:devices:detail', device_id=device.id)
    return render(request, 'panel/devices/detail.html', {'device': device})


@staff_member_required(login_url='/admin/login/')
def device_new(request):
    if request.method == 'POST':
        device_id = (request.POST.get('id') or '').strip()[:64]
        name = (request.POST.get('name') or '').strip()[:128]
        desired_git_ref = (request.POST.get('desired_git_ref') or 'main').strip()[:64]
        if not device_id:
            messages.error(request, 'ID is required.')
            return render(request, 'panel/devices/new.html', {
                'form': {'id': device_id, 'name': name, 'desired_git_ref': desired_git_ref},
            })
        if Device.objects.filter(id=device_id).exists():
            messages.error(request, f'Device {device_id!r} already exists.')
            return render(request, 'panel/devices/new.html', {
                'form': {'id': device_id, 'name': name, 'desired_git_ref': desired_git_ref},
            })
        device = Device.objects.create(id=device_id, name=name, desired_git_ref=desired_git_ref)
        messages.success(request, 'Device created. Copy the token from the detail page into the device now.')
        return redirect('panel:devices:detail', device_id=device.id)
    return render(request, 'panel/devices/new.html', {'form': {'desired_git_ref': 'main'}})
