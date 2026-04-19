"""Device CRUD — ported from the old views_panel.py."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from api import github_refs
from api.models import Device


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

    context = {
        'device': device,
        'gh_enabled': github_refs.enabled(),
        'gh_commits': github_refs.recent_commits() if github_refs.enabled() else [],
        'gh_branches': github_refs.branches() if github_refs.enabled() else [],
        'gh_tags': github_refs.tags() if github_refs.enabled() else [],
        'gh_reported_commit': (
            github_refs.commit_info(device.last_reported_ref)
            if github_refs.enabled() and device.last_reported_ref else None
        ),
        'gh_desired_commit': (
            github_refs.commit_info(device.desired_git_ref)
            if github_refs.enabled() and device.desired_git_ref else None
        ),
    }
    return render(request, 'panel/devices/detail.html', context)


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
