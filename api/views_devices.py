"""Custom dashboard for managing remote display devices.

Replaces the default Django admin for the Device model. Staff-only. Tailwind
via CDN keeps the build surface zero.
"""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Device


@staff_member_required(login_url='/admin/login/')
def device_list(request):
    devices = Device.objects.all().order_by('id')
    return render(request, 'devices/list.html', {'devices': devices})


@staff_member_required(login_url='/admin/login/')
def device_detail(request, device_id):
    device = get_object_or_404(Device, id=device_id)

    if request.method == 'POST':
        device.name = (request.POST.get('name') or '').strip()[:128]
        device.desired_git_ref = (request.POST.get('desired_git_ref') or 'main').strip()[:64]
        device.save(update_fields=['name', 'desired_git_ref', 'updated_at'])
        messages.success(request, 'Device updated.')
        return redirect('devices:detail', device_id=device.id)

    return render(request, 'devices/detail.html', {'device': device})


@staff_member_required(login_url='/admin/login/')
def device_new(request):
    if request.method == 'POST':
        device_id = (request.POST.get('id') or '').strip()[:64]
        name = (request.POST.get('name') or '').strip()[:128]
        desired_git_ref = (request.POST.get('desired_git_ref') or 'main').strip()[:64]
        if not device_id:
            messages.error(request, 'ID is required.')
            return render(request, 'devices/new.html', {
                'form': {'id': device_id, 'name': name, 'desired_git_ref': desired_git_ref},
            })
        if Device.objects.filter(id=device_id).exists():
            messages.error(request, f'Device {device_id!r} already exists.')
            return render(request, 'devices/new.html', {
                'form': {'id': device_id, 'name': name, 'desired_git_ref': desired_git_ref},
            })
        device = Device.objects.create(id=device_id, name=name, desired_git_ref=desired_git_ref)
        messages.success(request, f'Device created. Token is on the detail page — copy it to the device now.')
        return redirect('devices:detail', device_id=device.id)

    return render(request, 'devices/new.html', {'form': {'desired_git_ref': 'main'}})
