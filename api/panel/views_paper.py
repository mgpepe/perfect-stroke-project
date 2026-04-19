"""Paper CRUD with image upload and FK pickers."""

from decimal import Decimal

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from api.models import (
    Brand, BrandModel, Color, Paper, PaperMaterial, PaperSurface, Store,
)
from .uploads import upload_single_image


@staff_member_required(login_url='/admin/login/')
def paper_list(request):
    qs = Paper.objects.select_related(
        'brand', 'brand_model', 'color', 'paper_material', 'paper_surface', 'image'
    ).order_by('brand__name', 'verbose_name')
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(
            Q(verbose_name__icontains=query) | Q(ref__icontains=query)
            | Q(brand__name__icontains=query)
        )
    return render(request, 'panel/paper/list.html', {
        'papers': qs[:500],
        'query': query,
        'total': qs.count(),
    })


def _form_context():
    return {
        'brands': Brand.objects.order_by('name'),
        'brand_models': BrandModel.objects.select_related('brand').order_by('brand__name', 'name'),
        'colors': Color.objects.order_by('name'),
        'stores': Store.objects.order_by('name'),
        'paper_materials': PaperMaterial.objects.order_by('name'),
        'paper_surfaces': PaperSurface.objects.order_by('name'),
    }


def _apply_paper(paper, post, files):
    paper.verbose_name = (post.get('verbose_name') or '').strip()[:500]
    paper.ref = (post.get('ref') or '').strip()[:255]
    paper.original_size = (post.get('original_size') or '').strip()[:255]
    paper.gsm = _decimal(post.get('gsm'))
    paper.price = _decimal(post.get('price'))
    paper.brand = _fk(Brand, post.get('brand'))
    paper.brand_model = _fk(BrandModel, post.get('brand_model'))
    paper.color = _fk(Color, post.get('color'))
    paper.paper_material = _fk(PaperMaterial, post.get('paper_material'))
    paper.paper_surface = _fk(PaperSurface, post.get('paper_surface'))
    paper.store = _fk(Store, post.get('store'))

    image = files.get('image')
    if image:
        paper.image = upload_single_image(image, path=f'papers/{paper.pk or "new"}', file_type='paper')


@staff_member_required(login_url='/admin/login/')
def paper_new(request):
    if request.method == 'POST':
        paper = Paper()
        paper.save()
        try:
            _apply_paper(paper, request.POST, request.FILES)
            paper.save()
        except Exception as exc:
            paper.delete()
            messages.error(request, f'Create failed: {exc}')
            return redirect('panel:papers:list')
        messages.success(request, 'Paper created.')
        return redirect('panel:papers:detail', pk=paper.pk)
    return render(request, 'panel/paper/new.html', _form_context())


@staff_member_required(login_url='/admin/login/')
def paper_detail(request, pk):
    paper = get_object_or_404(
        Paper.objects.select_related(
            'brand', 'brand_model', 'color', 'paper_material', 'paper_surface', 'store', 'image'
        ),
        pk=pk,
    )
    if request.method == 'POST':
        _apply_paper(paper, request.POST, request.FILES)
        paper.save()
        messages.success(request, 'Paper updated.')
        return redirect('panel:papers:detail', pk=paper.pk)

    ctx = _form_context()
    ctx['paper'] = paper
    return render(request, 'panel/paper/detail.html', ctx)


@staff_member_required(login_url='/admin/login/')
def paper_delete(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    if request.method == 'POST':
        label = str(paper)
        paper.delete()
        messages.success(request, f'Deleted paper "{label}".')
        return redirect('panel:papers:list')
    return render(request, 'panel/paper/delete.html', {'paper': paper})


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
