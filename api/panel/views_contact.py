"""Contact CRUD. The detail page lists that contact's purchases."""

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from api.models import Contact


@staff_member_required(login_url='/admin/login/')
def contact_list(request):
    qs = Contact.objects.annotate(sale_count=Count('sales')).order_by('last_name', 'first_name')
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
            | Q(email__icontains=query) | Q(phone__icontains=query)
        )
    return render(request, 'panel/contact/list.html', {
        'contacts': qs[:500],
        'query': query,
        'total': qs.count(),
    })


def _apply_contact(contact, post):
    contact.first_name = (post.get('first_name') or '').strip()[:128]
    contact.last_name = (post.get('last_name') or '').strip()[:128]
    contact.email = (post.get('email') or '').strip()[:254]
    contact.phone = (post.get('phone') or '').strip()[:64]
    contact.notes = (post.get('notes') or '').strip()


@staff_member_required(login_url='/admin/login/')
def contact_new(request):
    if request.method == 'POST':
        contact = Contact()
        _apply_contact(contact, request.POST)
        if not contact.first_name:
            messages.error(request, 'First name is required.')
            return render(request, 'panel/contact/new.html', {'contact': contact})
        contact.save()
        messages.success(request, 'Contact created.')
        return redirect('panel:contacts:detail', pk=contact.pk)
    return render(request, 'panel/contact/new.html', {'contact': None})


@staff_member_required(login_url='/admin/login/')
def contact_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        _apply_contact(contact, request.POST)
        if not contact.first_name:
            messages.error(request, 'First name is required.')
        else:
            contact.save()
            messages.success(request, 'Contact updated.')
        return redirect('panel:contacts:detail', pk=contact.pk)

    from api.panel.images import stroke_url
    sales = list(
        contact.sales
        .select_related('stroke')
        .order_by('-sold_at', '-created_at')
    )
    for s in sales:
        s.thumb_url = stroke_url(s.stroke, '600')
    total_revenue = sum((s.price or 0) for s in sales)

    return render(request, 'panel/contact/detail.html', {
        'contact': contact,
        'sales': sales,
        'total_revenue': total_revenue,
    })


@staff_member_required(login_url='/admin/login/')
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        if contact.sales.exists():
            messages.error(request, 'This contact has purchases. Remove them first.')
            return redirect('panel:contacts:detail', pk=contact.pk)
        label = str(contact)
        contact.delete()
        messages.success(request, f'Deleted contact "{label}".')
        return redirect('panel:contacts:list')
    return render(request, 'panel/contact/delete.html', {
        'contact': contact,
        'sale_count': contact.sales.count(),
    })
