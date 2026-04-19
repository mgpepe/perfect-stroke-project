"""Tool CRUD with image upload and FK pickers."""

from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from api.models import (
    Brand, BrandModel, BrushHairType, QualityGrade, Store, Tool, ToolShape,
    ToolSize, ToolType,
)
from .uploads import upload_single_image


@staff_member_required(login_url='/admin/login/')
def tool_list(request):
    qs = Tool.objects.select_related(
        'brand', 'type', 'shape', 'size', 'brush_hair_type', 'image'
    ).order_by('brand__name', 'id')
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(
            Q(brand__name__icontains=query) | Q(type__name__icontains=query)
            | Q(shape__name__icontains=query)
        )
    return render(request, 'panel/tool/list.html', {
        'tools': qs[:500],
        'query': query,
        'total': qs.count(),
    })


def _form_context():
    return {
        'brands': Brand.objects.order_by('name'),
        'brand_models': BrandModel.objects.select_related('brand').order_by('brand__name', 'name'),
        'shapes': ToolShape.objects.select_related('tool_type').order_by('tool_type__name', 'name'),
        'types': ToolType.objects.order_by('name'),
        'sizes': ToolSize.objects.select_related('tool_type').order_by('tool_type__name', 'size'),
        'brush_hair_types': BrushHairType.objects.order_by('name'),
        'stores': Store.objects.order_by('name'),
        'quality_grades': QualityGrade.choices,
    }


def _apply_tool(tool, post, files):
    tool.brand = _fk(Brand, post.get('brand'))
    tool.model = _fk(BrandModel, post.get('model'))
    tool.shape = _fk(ToolShape, post.get('shape'))
    tool.brush_hair_type = _fk(BrushHairType, post.get('brush_hair_type'))
    tool.type = _fk(ToolType, post.get('type'))
    tool.size = _fk(ToolSize, post.get('size'))
    tool.store = _fk(Store, post.get('store'))
    tool.price = _decimal(post.get('price'))
    tool.quality = _int(post.get('quality'), None)

    image = files.get('image')
    if image:
        tool.image = upload_single_image(image, path=f'tools/{tool.pk or "new"}', file_type='tool')


@staff_member_required(login_url='/admin/login/')
def tool_new(request):
    if request.method == 'POST':
        tool = Tool()
        tool.save()
        try:
            _apply_tool(tool, request.POST, request.FILES)
            tool.save()
        except Exception as exc:
            tool.delete()
            messages.error(request, f'Create failed: {exc}')
            return redirect('panel:tools:list')
        messages.success(request, 'Tool created.')
        return redirect('panel:tools:detail', pk=tool.pk)
    return render(request, 'panel/tool/new.html', _form_context())


@staff_member_required(login_url='/admin/login/')
def tool_detail(request, pk):
    tool = get_object_or_404(
        Tool.objects.select_related(
            'brand', 'model', 'shape', 'brush_hair_type', 'type', 'size', 'store', 'image'
        ),
        pk=pk,
    )
    if request.method == 'POST':
        _apply_tool(tool, request.POST, request.FILES)
        tool.save()
        messages.success(request, 'Tool updated.')
        return redirect('panel:tools:detail', pk=tool.pk)

    ctx = _form_context()
    ctx['tool'] = tool
    return render(request, 'panel/tool/detail.html', ctx)


@staff_member_required(login_url='/admin/login/')
def tool_delete(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    if request.method == 'POST':
        label = str(tool.pk)
        tool.delete()
        messages.success(request, f'Deleted tool {label}.')
        return redirect('panel:tools:list')
    return render(request, 'panel/tool/delete.html', {'tool': tool})


def _int(value, default):
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _decimal(value):
    if value in (None, ''):
        return None
    try:
        return Decimal(value)
    except Exception:
        return None


def _fk(model, value):
    if not value:
        return None
    return model.objects.filter(pk=value).first()
