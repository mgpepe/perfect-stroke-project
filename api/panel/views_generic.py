"""Generic list/new/edit/delete views driven by registry.ModelPanel."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .registry import Field, LOOKUPS_BY_SLUG


def _get_panel(slug: str):
    panel = LOOKUPS_BY_SLUG.get(slug)
    if panel is None:
        raise Http404(f"No panel registered for slug {slug!r}")
    return panel


def _apply_search(qs, panel, query):
    if not query or not panel.search_fields:
        return qs
    q = Q()
    for f in panel.search_fields:
        q |= Q(**{f'{f}__icontains': query})
    return qs.filter(q)


def _fk_choices(field: Field):
    qs = field.fk_model.objects.all().order_by(field.fk_order)
    return [(obj.pk, getattr(obj, field.fk_label, str(obj))) for obj in qs]


def _bind_form(panel, post_data):
    """Return (cleaned, errors) dict pair from POST data per panel.fields."""
    cleaned = {}
    errors = {}
    for f in panel.fields:
        raw = post_data.get(f.name, '').strip() if f.kind != 'checkbox' else post_data.get(f.name)
        if f.kind == 'checkbox':
            cleaned[f.name] = bool(raw)
            continue
        if not raw:
            if f.required:
                errors[f.name] = 'Required.'
            cleaned[f.name] = None if f.kind in ('fk', 'number', 'select') else ''
            continue
        if f.kind == 'fk':
            try:
                cleaned[f.name] = f.fk_model.objects.get(pk=raw)
            except f.fk_model.DoesNotExist:
                errors[f.name] = 'Invalid selection.'
        elif f.kind == 'number':
            try:
                cleaned[f.name] = int(raw)
            except ValueError:
                errors[f.name] = 'Must be a number.'
        elif f.kind == 'select':
            cleaned[f.name] = raw
        else:
            cleaned[f.name] = raw
    return cleaned, errors


def _apply_to_instance(instance, panel, cleaned):
    for f in panel.fields:
        if f.kind == 'fk':
            setattr(instance, f.name, cleaned.get(f.name))
        else:
            setattr(instance, f.name, cleaned.get(f.name))
    return instance


def _field_context(panel, instance=None, post_data=None):
    """Build per-field context for the template."""
    ctx = []
    for f in panel.fields:
        if post_data is not None:
            value = post_data.get(f.name, '')
        elif instance is not None:
            raw = getattr(instance, f.name, None)
            if f.kind == 'fk' and raw is not None:
                value = raw.pk
            elif f.kind == 'checkbox':
                value = bool(raw)
            else:
                value = '' if raw is None else raw
        else:
            value = '' if f.kind != 'checkbox' else False

        item = {
            'name': f.name,
            'label': f.label,
            'kind': f.kind,
            'required': f.required,
            'help': f.help,
            'placeholder': f.placeholder,
            'value': value,
            'choices': None,
        }
        if f.kind == 'fk':
            item['choices'] = _fk_choices(f)
        elif f.kind == 'select':
            item['choices'] = f.choices or []
        ctx.append(item)
    return ctx


def _render_columns(panel, objects):
    """Serialize each row into a list of cell dicts the template can render."""
    rows = []
    for obj in objects:
        cells = []
        for col in panel.columns or [_default_name_column(panel)]:
            cells.append({
                'label': col.label,
                'mono': col.mono,
                'classes': col.classes,
                'kind': _column_kind(col),
                'value': _column_value(col, obj),
            })
        rows.append({'obj': obj, 'cells': cells})
    return rows


def _default_name_column(panel):
    from .registry import Column
    return Column('Name', panel.fields[0].name if panel.fields else 'id')


def _column_kind(col):
    if col.accessor == '__swatch__':
        return 'swatch'
    if col.accessor == '__file_preview__':
        return 'file_preview'
    return 'text'


def _column_value(col, obj):
    if col.accessor == '__swatch__':
        return getattr(obj, 'hex_code', '') or ''
    if col.accessor == '__file_preview__':
        return getattr(obj, 'url_path', '') or ''
    return col.get(obj)


# ─── Views ──────────────────────────────────────────────────────

@staff_member_required(login_url='/admin/login/')
def generic_list(request, slug):
    panel = _get_panel(slug)
    query = request.GET.get('q', '').strip()
    qs = _apply_search(panel.queryset(), panel, query)
    total = qs.count()
    qs = qs[:500]  # sanity cap; most tables are small
    rows = _render_columns(panel, qs)
    columns = panel.columns or [_default_name_column(panel)]
    return render(request, 'panel/generic/list.html', {
        'panel': panel,
        'rows': rows,
        'columns': columns,
        'query': query,
        'total': total,
        'truncated': total > 500,
    })


@staff_member_required(login_url='/admin/login/')
def generic_new(request, slug):
    panel = _get_panel(slug)
    if request.method == 'POST':
        cleaned, errors = _bind_form(panel, request.POST)
        if not errors:
            instance = panel.model()
            _apply_to_instance(instance, panel, cleaned)
            instance.save()
            messages.success(request, f'{panel.singular} created.')
            return redirect('panel:generic:' + slug + ':detail', pk=instance.pk)
        for name, msg in errors.items():
            messages.error(request, f'{name}: {msg}')
        return render(request, 'panel/generic/form.html', {
            'panel': panel,
            'fields': _field_context(panel, post_data=request.POST),
            'is_new': True,
            'errors': errors,
        })
    return render(request, 'panel/generic/form.html', {
        'panel': panel,
        'fields': _field_context(panel),
        'is_new': True,
        'errors': {},
    })


@staff_member_required(login_url='/admin/login/')
def generic_detail(request, slug, pk):
    panel = _get_panel(slug)
    instance = get_object_or_404(panel.model, pk=pk)
    if request.method == 'POST':
        cleaned, errors = _bind_form(panel, request.POST)
        if not errors:
            _apply_to_instance(instance, panel, cleaned)
            instance.save()
            messages.success(request, f'{panel.singular} updated.')
            return redirect('panel:generic:' + slug + ':detail', pk=instance.pk)
        for name, msg in errors.items():
            messages.error(request, f'{name}: {msg}')
        return render(request, 'panel/generic/form.html', {
            'panel': panel,
            'instance': instance,
            'fields': _field_context(panel, instance=instance, post_data=request.POST),
            'is_new': False,
            'errors': errors,
        })
    return render(request, 'panel/generic/form.html', {
        'panel': panel,
        'instance': instance,
        'fields': _field_context(panel, instance=instance),
        'is_new': False,
        'errors': {},
    })


@staff_member_required(login_url='/admin/login/')
def generic_delete(request, slug, pk):
    panel = _get_panel(slug)
    instance = get_object_or_404(panel.model, pk=pk)
    if request.method == 'POST':
        label = str(instance)
        instance.delete()
        messages.success(request, f'{panel.singular} "{label}" deleted.')
        return redirect('panel:generic:' + slug + ':list')
    return render(request, 'panel/generic/delete.html', {
        'panel': panel,
        'instance': instance,
    })
