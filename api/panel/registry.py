"""Registry for the lookup-table CRUD screens under /panel/.

Hero models (Stroke, Paint, Paper, Tool) are hand-built — they have
image uploads, multiple FKs, and inline M2M editors that don't fit a
generic shape. Everything else (Brand, Color, Pigment, …) is described
here and rendered by `views_generic`.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from django.db.models import Model

from api.models import (
    Brand, BrandModel, BrushHairType, Color, File, PaperMaterial,
    PaperSurface, Pigment, Store, ToolShape, ToolSize, ToolType,
)


@dataclass
class Column:
    """A column in the list view."""
    label: str
    accessor: str  # dotted path (e.g. 'brand.name')
    mono: bool = False
    classes: str = ""

    def get(self, obj: Any) -> Any:
        value = obj
        for part in self.accessor.split('.'):
            if value is None:
                return None
            value = getattr(value, part, None)
        return value


@dataclass
class Field:
    """A form field."""
    name: str
    label: str = ""
    kind: str = "text"  # text | textarea | number | checkbox | url | hex | select | fk
    required: bool = False
    help: str = ""
    choices: Optional[list] = None  # for kind='select'; [(value, label), ...]
    fk_model: Optional[type] = None  # for kind='fk'
    fk_order: str = "name"
    fk_label: str = "name"  # attribute used as display label
    placeholder: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = self.name.replace('_', ' ').capitalize()


@dataclass
class ModelPanel:
    model: type
    slug: str
    singular: str
    plural: str
    group: str = "taxonomy"  # sidebar group key
    icon: str = "tag"
    columns: list = field(default_factory=list)
    fields: list = field(default_factory=list)
    order_by: tuple = ("name",)
    search_fields: tuple = ("name",)
    description: str = ""

    def queryset(self):
        qs = self.model.objects.all()
        if self.order_by:
            qs = qs.order_by(*self.order_by)
        return qs


# ─── Registry ────────────────────────────────────────────────────

LOOKUPS = [
    ModelPanel(
        model=Brand, slug='brands', singular='Brand', plural='Brands',
        description='Manufacturer names shared across paints, papers, and tools.',
        columns=[
            Column('Name', 'name'),
            Column('Models', 'models.count', mono=True, classes='text-zinc-500 w-24'),
            Column('Paints', 'paints.count', mono=True, classes='text-zinc-500 w-24'),
        ],
        fields=[Field('name', required=True, placeholder='e.g. Winsor & Newton')],
    ),
    ModelPanel(
        model=BrandModel, slug='brand-models', singular='Brand model', plural='Brand models',
        description='A specific product line under a brand (e.g. "Professional Watercolour").',
        columns=[
            Column('Name', 'name'),
            Column('Brand', 'brand.name', classes='text-zinc-400'),
        ],
        fields=[
            Field('name', required=True),
            Field('brand', kind='fk', required=True, fk_model=Brand),
        ],
        order_by=('brand__name', 'name'),
        search_fields=('name', 'brand__name'),
    ),
    ModelPanel(
        model=Color, slug='colors', singular='Color', plural='Colors',
        icon='swatch',
        columns=[
            Column('Swatch', '__swatch__', classes='w-20'),
            Column('Name', 'name'),
            Column('Hex', 'hex_code', mono=True, classes='text-zinc-400'),
        ],
        fields=[
            Field('name', required=True),
            Field('hex_code', label='Hex code', kind='hex',
                  help='Six-digit hex with leading #, e.g. #a33c2f'),
        ],
    ),
    ModelPanel(
        model=Store, slug='stores', singular='Store', plural='Stores',
        icon='shop',
        columns=[
            Column('Name', 'name'),
            Column('URL', 'url', classes='text-zinc-500 truncate max-w-xs'),
        ],
        fields=[
            Field('name', required=True),
            Field('url', kind='url'),
        ],
    ),
    ModelPanel(
        model=Pigment, slug='pigments', singular='Pigment', plural='Pigments',
        icon='droplet',
        columns=[
            Column('Name', 'name'),
            Column('Color', 'color.name', classes='text-zinc-400'),
        ],
        fields=[
            Field('name', required=True),
            Field('color', kind='fk', required=True, fk_model=Color),
        ],
        search_fields=('name', 'color__name'),
    ),
    ModelPanel(
        model=PaperMaterial, slug='paper-materials',
        singular='Paper material', plural='Paper materials',
        description='e.g. Cotton, Cellulose, Mixed.',
        fields=[Field('name', required=True)],
    ),
    ModelPanel(
        model=PaperSurface, slug='paper-surfaces',
        singular='Paper surface', plural='Paper surfaces',
        description='e.g. Hot pressed, Cold pressed, Rough.',
        fields=[Field('name', required=True)],
    ),
    ModelPanel(
        model=ToolType, slug='tool-types', singular='Tool type', plural='Tool types',
        description='e.g. Brush, Pencil, Palette knife.',
        fields=[Field('name', required=True)],
    ),
    ModelPanel(
        model=ToolShape, slug='tool-shapes', singular='Tool shape', plural='Tool shapes',
        columns=[
            Column('Name', 'name'),
            Column('Tool type', 'tool_type.name', classes='text-zinc-400'),
        ],
        fields=[
            Field('name', required=True),
            Field('tool_type', label='Tool type', kind='fk', required=True, fk_model=ToolType),
        ],
        search_fields=('name', 'tool_type__name'),
    ),
    ModelPanel(
        model=ToolSize, slug='tool-sizes', singular='Tool size', plural='Tool sizes',
        columns=[
            Column('Size', 'size', mono=True),
            Column('Tool type', 'tool_type.name', classes='text-zinc-400'),
        ],
        fields=[
            Field('size', required=True, placeholder='e.g. 8, 1/4", 30mm'),
            Field('tool_type', label='Tool type', kind='fk', required=True, fk_model=ToolType),
        ],
        order_by=('tool_type__name', 'size'),
        search_fields=('size', 'tool_type__name'),
    ),
    ModelPanel(
        model=BrushHairType, slug='brush-hair-types',
        singular='Brush hair', plural='Brush hair types',
        description='e.g. Kolinsky sable, Synthetic, Squirrel.',
        fields=[Field('name', required=True)],
    ),
    ModelPanel(
        model=File, slug='files', singular='File', plural='Files',
        group='files', icon='file',
        description='Images uploaded to Cloudflare R2. Delete here to soft-remove from listings.',
        columns=[
            Column('Preview', '__file_preview__', classes='w-24'),
            Column('Name', 'original_file_name', classes='truncate max-w-xs'),
            Column('Type', 'type', classes='text-zinc-500'),
            Column('Uploaded', 'created_on', classes='text-zinc-500'),
        ],
        fields=[
            Field('original_file_name', label='Name', required=True),
            Field('url_path', label='URL', kind='url'),
            Field('type'),
            Field('is_deleted', label='Deleted', kind='checkbox'),
        ],
        order_by=('-created_on',),
        search_fields=('original_file_name', 'type'),
    ),
]


LOOKUPS_BY_SLUG = {p.slug: p for p in LOOKUPS}


# ─── Sidebar navigation ──────────────────────────────────────────

NAV_GROUPS = [
    {
        'key': 'operations',
        'label': 'Operations',
        'items': [
            {'slug': 'modify', 'label': 'Modify', 'icon': 'sparkle',
             'url_name': 'panel:modify:list', 'match': 'modify'},
            {'slug': 'devices', 'label': 'Devices', 'icon': 'device',
             'url_name': 'panel:devices:list', 'match': 'device'},
        ],
    },
    {
        'key': 'artifacts',
        'label': 'Artifacts',
        'items': [
            {'slug': 'strokes', 'label': 'Strokes', 'icon': 'brush',
             'url_name': 'panel:strokes:list', 'match': 'stroke'},
            {'slug': 'paints', 'label': 'Paints', 'icon': 'droplet',
             'url_name': 'panel:paints:list', 'match': 'paint'},
            {'slug': 'papers', 'label': 'Papers', 'icon': 'paper',
             'url_name': 'panel:papers:list', 'match': 'paper'},
            {'slug': 'tools', 'label': 'Tools', 'icon': 'wrench',
             'url_name': 'panel:tools:list', 'match': 'tool'},
        ],
    },
    {
        'key': 'sales',
        'label': 'Sales',
        'items': [
            {'slug': 'contacts', 'label': 'Contacts', 'icon': 'user',
             'url_name': 'panel:contacts:list', 'match': 'contact'},
        ],
    },
    {
        'key': 'taxonomy',
        'label': 'Taxonomy',
        'items': [
            {'slug': 'brands', 'label': 'Brands', 'icon': 'tag'},
            {'slug': 'brand-models', 'label': 'Brand models', 'icon': 'tag'},
            {'slug': 'colors', 'label': 'Colors', 'icon': 'swatch'},
            {'slug': 'pigments', 'label': 'Pigments', 'icon': 'droplet'},
            {'slug': 'stores', 'label': 'Stores', 'icon': 'shop'},
            {'slug': 'paper-materials', 'label': 'Paper materials', 'icon': 'tag'},
            {'slug': 'paper-surfaces', 'label': 'Paper surfaces', 'icon': 'tag'},
            {'slug': 'tool-types', 'label': 'Tool types', 'icon': 'tag'},
            {'slug': 'tool-shapes', 'label': 'Tool shapes', 'icon': 'tag'},
            {'slug': 'tool-sizes', 'label': 'Tool sizes', 'icon': 'tag'},
            {'slug': 'brush-hair-types', 'label': 'Brush hair', 'icon': 'tag'},
        ],
    },
    {
        'key': 'storage',
        'label': 'Storage',
        'items': [
            {'slug': 'files', 'label': 'Files', 'icon': 'file'},
        ],
    },
]


def nav_for_template():
    """Return NAV_GROUPS with URL strings resolved for registered lookups."""
    from django.urls import reverse
    resolved = []
    for group in NAV_GROUPS:
        items = []
        for item in group['items']:
            it = dict(item)
            if 'url_name' not in it:
                it['url_name'] = f"panel:generic:{it['slug']}:list"
            if 'match' not in it:
                it['match'] = it['slug']
            items.append(it)
        resolved.append({**group, 'items': items})
    return resolved
