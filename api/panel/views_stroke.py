"""Hand-built Stroke admin — thumbnails, R2 upload, inline paints/tools."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from api.models import Paint, Paper, Stroke, StrokePaint, StrokeTool, Tool
from .images import annotate_strokes, stroke_url
from .uploads import attach_stroke_image_set, upload_stroke_image_set


PER_PAGE = 100


def _paginate(qs, page):
    start = (page - 1) * PER_PAGE
    return qs[start:start + PER_PAGE]


@staff_member_required(login_url='/admin/login/')
def stroke_list(request):
    qs = (
        Stroke.objects.select_related('image_600', 'paper')
        .order_by('order_id', 'id')
    )
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(tags__icontains=query))
    try:
        page = max(1, int(request.GET.get('page', '1')))
    except ValueError:
        page = 1
    total = qs.count()
    strokes = list(_paginate(qs, page))
    annotate_strokes(strokes, sizes=('600',))
    return render(request, 'panel/stroke/list.html', {
        'strokes': strokes,
        'query': query,
        'page': page,
        'total': total,
        'per_page': PER_PAGE,
        'has_next': page * PER_PAGE < total,
        'has_prev': page > 1,
    })


@staff_member_required(login_url='/admin/login/')
def stroke_new(request):
    if request.method == 'POST':
        stroke = Stroke.objects.create(
            title=(request.POST.get('title') or '').strip()[:255],
            description=(request.POST.get('description') or '').strip(),
            tags=(request.POST.get('tags') or '').strip()[:500],
            order_id=_int(request.POST.get('order_id'), 0),
            paper=_fk(Paper, request.POST.get('paper')),
        )
        image = request.FILES.get('image')
        if image:
            try:
                file_set = upload_stroke_image_set(image)
                attach_stroke_image_set(stroke, file_set)
            except Exception as exc:
                messages.error(request, f'Image upload failed: {exc}')
        messages.success(request, 'Stroke created.')
        return redirect('panel:strokes:detail', pk=stroke.pk)
    return render(request, 'panel/stroke/new.html', {
        'papers': Paper.objects.select_related('brand').order_by('verbose_name', 'ref'),
    })


@staff_member_required(login_url='/admin/login/')
def stroke_detail(request, pk):
    stroke = get_object_or_404(
        Stroke.objects.select_related(
            'paper', 'image_600', 'image_1800', 'image_2500', 'image_original'
        ),
        pk=pk,
    )
    if request.method == 'POST':
        action = request.POST.get('action', 'save')

        if action == 'save':
            stroke.title = (request.POST.get('title') or '').strip()[:255]
            stroke.description = (request.POST.get('description') or '').strip()
            stroke.tags = (request.POST.get('tags') or '').strip()[:500]
            stroke.order_id = _int(request.POST.get('order_id'), stroke.order_id)
            stroke.paper = _fk(Paper, request.POST.get('paper'))
            stroke.save()
            messages.success(request, 'Stroke updated.')

        elif action == 'upload_image':
            image = request.FILES.get('image')
            if not image:
                messages.error(request, 'Choose an image file first.')
            else:
                try:
                    file_set = upload_stroke_image_set(image)
                    attach_stroke_image_set(stroke, file_set)
                    messages.success(request, 'Image uploaded to R2.')
                except Exception as exc:
                    messages.error(request, f'Upload failed: {exc}')

        elif action == 'add_paint':
            paint_id = request.POST.get('paint_id')
            if paint_id:
                paint = _fk(Paint, paint_id)
                if paint and not StrokePaint.objects.filter(stroke=stroke, paint=paint).exists():
                    StrokePaint.objects.create(stroke=stroke, paint=paint)
                    messages.success(request, f'Added paint {paint.name}.')

        elif action == 'remove_paint':
            StrokePaint.objects.filter(stroke=stroke, pk=request.POST.get('sp_id')).delete()
            messages.success(request, 'Paint removed.')

        elif action == 'add_tool':
            tool_id = request.POST.get('tool_id')
            if tool_id:
                tool = _fk(Tool, tool_id)
                if tool and not StrokeTool.objects.filter(stroke=stroke, tool=tool).exists():
                    StrokeTool.objects.create(stroke=stroke, tool=tool)
                    messages.success(request, 'Tool added.')

        elif action == 'remove_tool':
            StrokeTool.objects.filter(stroke=stroke, pk=request.POST.get('st_id')).delete()
            messages.success(request, 'Tool removed.')

        return redirect('panel:strokes:detail', pk=stroke.pk)

    stroke_paints = (
        StrokePaint.objects.filter(stroke=stroke)
        .select_related('paint__brand', 'paint__color').order_by('paint__name')
    )
    stroke_tools = (
        StrokeTool.objects.filter(stroke=stroke)
        .select_related('tool__brand', 'tool__type').order_by('tool__brand__name')
    )
    return render(request, 'panel/stroke/detail.html', {
        'stroke': stroke,
        'stroke_paints': stroke_paints,
        'stroke_tools': stroke_tools,
        'papers': Paper.objects.select_related('brand').order_by('verbose_name', 'ref'),
        'paints': Paint.objects.select_related('brand', 'color').order_by('brand__name', 'name'),
        'tools': Tool.objects.select_related('brand', 'type').order_by('brand__name', 'id'),
        'hero_url': stroke_url(stroke, '1800') or stroke_url(stroke, '600') or stroke_url(stroke, 'original'),
        'image_urls': {
            '100': stroke_url(stroke, '100'),
            '600': stroke_url(stroke, '600'),
            '1800': stroke_url(stroke, '1800'),
            '2500': stroke_url(stroke, '2500'),
            'original': stroke_url(stroke, 'original'),
        },
    })


@staff_member_required(login_url='/admin/login/')
def stroke_delete(request, pk):
    stroke = get_object_or_404(Stroke, pk=pk)
    if request.method == 'POST':
        label = str(stroke)
        stroke.delete()
        messages.success(request, f'Deleted stroke "{label}".')
        return redirect('panel:strokes:list')
    return render(request, 'panel/stroke/delete.html', {'stroke': stroke})


# ─── Helpers ────────────────────────────────────────────────────

def _int(value, default):
    try:
        return int(value) if value not in (None, '') else default
    except (TypeError, ValueError):
        return default


def _fk(model, value):
    if not value:
        return None
    try:
        return model.objects.filter(pk=value).first()
    except Exception:
        return None
