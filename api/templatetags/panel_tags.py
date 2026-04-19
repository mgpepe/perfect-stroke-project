from django import template
from django.urls import NoReverseMatch, reverse

from api.panel.images import absolute_url
from api.panel.registry import nav_for_template

register = template.Library()


@register.filter(name='r2url')
def r2url(value):
    """Normalize a File.url_path (which may be a relative R2 key) to a full URL."""
    return absolute_url(value)


@register.inclusion_tag('panel/_sidebar.html', takes_context=True)
def panel_sidebar(context):
    request = context.get('request')
    current = ''
    if request and request.resolver_match:
        current = request.resolver_match.view_name or ''

    groups = []
    for group in nav_for_template():
        items = []
        for item in group['items']:
            try:
                url = reverse(item['url_name'])
            except NoReverseMatch:
                url = '#'
            active = item['match'] in current
            items.append({**item, 'url': url, 'active': active})
        groups.append({**group, 'items': items})
    return {'groups': groups, 'request': request}


@register.filter
def get(d, key):
    try:
        return d[key]
    except (KeyError, TypeError):
        return ''
