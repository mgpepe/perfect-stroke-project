"""Paint CRUD with image upload, FK pickers, inline pigments."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from api.models import (
    Brand, BrandModel, Color, OpacityType, Paint, PaintType, Pigment,
    PigmentPaint, QualityGrade, Store,
)
from .uploads import upload_single_image


@staff_member_required(login_url='/admin/login/')
def paint_list(request):
    qs = Paint.objects.select_related('brand', 'brand_model', 'color', 'image').order_by('brand__name', 'name')
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(
            Q(name__icontains=query) | Q(ref_paint__icontains=query)
            | Q(ref_brand_color__icontains=query) | Q(brand__name__icontains=query)
        )
    return render(request, 'panel/paint/list.html', {
        'paints': qs[:500],
        'query': query,
        'total': qs.count(),
    })


def _form_context():
    return {
        'brands': Brand.objects.order_by('name'),
        'brand_models': BrandModel.objects.select_related('brand').order_by('brand__name', 'name'),
        'colors': Color.objects.order_by('name'),
        'stores': Store.objects.order_by('name'),
        'pigments': Pigment.objects.select_related('color').order_by('name'),
        'paint_types': PaintType.choices,
        'opacity_types': OpacityType.choices,
        'quality_grades': QualityGrade.choices,
    }


def _apply_paint(paint, post, files):
    paint.name = (post.get('name') or '').strip()[:255]
    paint.brand = _fk(Brand, post.get('brand'))
    paint.brand_model = _fk(BrandModel, post.get('brand_model'))
    paint.color = _fk(Color, post.get('color'))
    paint.store = _fk(Store, post.get('store'))
    paint.type = _int(post.get('type'), paint.type if paint.pk else 0)
    paint.opacity = _int(post.get('opacity'), None)
    paint.opacity_number = _int(post.get('opacity_number'), None)
    paint.quality = _int(post.get('quality'), None)
    paint.ref_paint = (post.get('ref_paint') or '').strip()[:255]
    paint.ref_brand_color = (post.get('ref_brand_color') or '').strip()[:255]
    paint.granulating = _tri(post.get('granulating'))
    paint.staining = _tri(post.get('staining'))
    paint.price = _decimal(post.get('price'))

    image = files.get('image')
    if image:
        paint.image = upload_single_image(image, path=f'paints/{paint.pk or "new"}', file_type='paint')


@staff_member_required(login_url='/admin/login/')
def paint_new(request):
    if request.method == 'POST':
        paint = Paint(name=(request.POST.get('name') or '').strip()[:255])
        paint.type = _int(request.POST.get('type'), 0)
        paint.save()
        try:
            _apply_paint(paint, request.POST, request.FILES)
            paint.save()
        except Exception as exc:
            paint.delete()
            messages.error(request, f'Create failed: {exc}')
            return redirect('panel:paints:list')
        messages.success(request, 'Paint created.')
        return redirect('panel:paints:detail', pk=paint.pk)
    return render(request, 'panel/paint/new.html', _form_context())


@staff_member_required(login_url='/admin/login/')
def paint_detail(request, pk):
    paint = get_object_or_404(
        Paint.objects.select_related('brand', 'brand_model', 'color', 'store', 'image'),
        pk=pk,
    )
    if request.method == 'POST':
        action = request.POST.get('action', 'save')
        if action == 'save':
            _apply_paint(paint, request.POST, request.FILES)
            paint.save()
            messages.success(request, 'Paint updated.')
        elif action == 'add_pigment':
            pigment_id = request.POST.get('pigment_id')
            if pigment_id:
                pig = _fk(Pigment, pigment_id)
                if pig and not PigmentPaint.objects.filter(paint=paint, pigment=pig).exists():
                    PigmentPaint.objects.create(paint=paint, pigment=pig)
                    messages.success(request, f'Added pigment {pig.name}.')
        elif action == 'remove_pigment':
            PigmentPaint.objects.filter(paint=paint, pk=request.POST.get('pp_id')).delete()
            messages.success(request, 'Pigment removed.')
        return redirect('panel:paints:detail', pk=paint.pk)

    ctx = _form_context()
    ctx['paint'] = paint
    ctx['pigment_paints'] = (
        PigmentPaint.objects.filter(paint=paint)
        .select_related('pigment__color').order_by('pigment__name')
    )
    return render(request, 'panel/paint/detail.html', ctx)


@staff_member_required(login_url='/admin/login/')
def paint_delete(request, pk):
    paint = get_object_or_404(Paint, pk=pk)
    if request.method == 'POST':
        label = paint.name
        paint.delete()
        messages.success(request, f'Deleted paint "{label}".')
        return redirect('panel:paints:list')
    return render(request, 'panel/paint/delete.html', {'paint': paint})


# ─── Helpers ────────────────────────────────────────────────────

def _int(value, default):
    if value in (None, ''):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _tri(value):
    """A tri-state bool from a <select> that yields '', 'true', 'false'."""
    if value == 'true':
        return True
    if value == 'false':
        return False
    return None


def _decimal(value):
    if value in (None, ''):
        return None
    try:
        from decimal import Decimal
        return Decimal(value)
    except Exception:
        return None


def _fk(model, value):
    if not value:
        return None
    return model.objects.filter(pk=value).first()
