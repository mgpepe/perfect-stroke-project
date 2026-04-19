"""/panel/modify/ — submit and monitor AI modification jobs."""

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from api.models import ModifyJob
from api.panel import builder


@staff_member_required(login_url='/admin/login/')
def modify_list(request):
    jobs = ModifyJob.objects.all()[:50]
    return render(request, 'panel/modify/list.html', {
        'jobs': jobs,
        'anthropic_configured': bool(settings.ANTHROPIC_API_KEY),
        'github_configured': bool(settings.GITHUB_TOKEN),
    })


@staff_member_required(login_url='/admin/login/')
def modify_new(request):
    if request.method == 'POST':
        prompt = (request.POST.get('prompt') or '').strip()
        if not prompt:
            messages.error(request, 'Prompt is required.')
            return render(request, 'panel/modify/new.html', {'form': {'prompt': prompt}})
        if not settings.ANTHROPIC_API_KEY:
            messages.error(request, 'ANTHROPIC_API_KEY is not configured on the server.')
            return redirect('panel:modify:list')
        if not settings.GITHUB_TOKEN:
            messages.error(request, 'GITHUB_TOKEN is not configured on the server.')
            return redirect('panel:modify:list')

        job = ModifyJob.objects.create(
            prompt=prompt,
            repo=settings.GITHUB_REPO,
            status='queued',
            model=settings.BUILDER_MODEL,
            max_cost_usd=settings.BUILDER_MAX_COST_USD,
            max_rounds=settings.BUILDER_MAX_ROUNDS,
            created_by=request.user if request.user.is_authenticated else None,
        )
        builder.start_job(job)
        return redirect('panel:modify:detail', job_id=job.id)

    return render(request, 'panel/modify/new.html', {'form': {}})


@staff_member_required(login_url='/admin/login/')
def modify_detail(request, job_id):
    job = get_object_or_404(ModifyJob, id=job_id)
    return render(request, 'panel/modify/detail.html', {'job': job})


@staff_member_required(login_url='/admin/login/')
def modify_job_json(request, job_id):
    """Live-polling endpoint for the detail page."""
    job = get_object_or_404(ModifyJob, id=job_id)
    return JsonResponse({
        'id': job.id,
        'status': job.status,
        'current_phase': job.current_phase,
        'round_num': job.round_num,
        'max_rounds': job.max_rounds,
        'cost_usd': job.cost_usd,
        'max_cost_usd': job.max_cost_usd,
        'commit_sha': job.commit_sha,
        'diff': job.diff,
        'error': job.error,
        'log': job.log,
        'is_terminal': job.is_terminal(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
    })
