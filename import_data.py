"""
Import SQL Server CSV exports into PostgreSQL via Django ORM.
Run: cd /Users/pp/www/perfect-stroke-project && source venv/bin/activate && python manage.py shell < import_data.py
"""
import csv
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perfectstroke.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from api.models import (
    Brand, BrandModel, Color, File, Store, PaperMaterial, PaperSurface,
    ToolType, ToolShape, ToolSize, BrushHairType, Pigment, PigmentPaint,
    Paint, Paper, Tool, Stroke, StrokePaint, StrokeTool,
)

User = get_user_model()

EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ps_export')


def read_csv(filename):
    """Read CSV, skip the sqlcmd separator row (second row with dashes)."""
    path = os.path.join(EXPORT_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for i, row in enumerate(reader):
            # Skip separator row (all values are dashes)
            if i == 0 and all(v.strip().replace('-', '') == '' for v in row.values()):
                continue
            rows.append({k: (v.strip() if v and v.strip() != 'NULL' else '') for k, v in row.items()})
        return rows


def null_or_val(val):
    """Return None for empty/NULL values."""
    if not val or val == 'NULL' or val == '':
        return None
    return val


def null_or_decimal(val):
    if not val or val == 'NULL' or val == '':
        return None
    return val


def null_or_int(val):
    if not val or val == 'NULL' or val == '':
        return None
    return int(val)


def null_or_bool(val):
    if not val or val == 'NULL' or val == '':
        return None
    return val == '1' or val.lower() == 'true'


def import_table(filename, model, field_map, label=None):
    """Generic import: field_map = {csv_col: (django_field, converter)}"""
    label = label or filename
    rows = read_csv(filename)
    objs = []
    for row in rows:
        kwargs = {}
        for csv_col, (django_field, converter) in field_map.items():
            kwargs[django_field] = converter(row.get(csv_col, ''))
        objs.append(model(**kwargs))
    model.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
    print(f'  {label}: {len(objs)} rows')


# ─── Import order matters (foreign keys) ─────────────────────────

print('Importing data...')

# 1. Users
rows = read_csv('Users.csv')
for row in rows:
    if User.objects.filter(username=row.get('UserName', '')).exists():
        continue
    user = User(
        username=row.get('UserName', ''),
        email=row.get('Email', ''),
        first_name=row.get('FirstName', ''),
        last_name=row.get('LastName', ''),
        picture_url=row.get('PictureUrl', '') or '',
        website=row.get('Website', '') or '',
        bio=row.get('Bio', '') or '',
        facebook_id=null_or_int(row.get('FacbookId')),
    )
    birthday = row.get('Birthday', '')
    if birthday and birthday != '' and not birthday.startswith('0001'):
        user.birthday = birthday[:10]
    user.set_unusable_password()
    user.save()
print(f'  Users: {len(rows)} rows')

# 2. Simple lookups (no FK dependencies)
import_table('Brands.csv', Brand, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
})

import_table('Colors.csv', Color, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
    'HexCode': ('hex_code', lambda v: v or ''),
})

import_table('Stores.csv', Store, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
    'Url': ('url', lambda v: v or ''),
})

import_table('PaperMaterials.csv', PaperMaterial, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
})

import_table('PaperSurfaces.csv', PaperSurface, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
})

import_table('ToolTypes.csv', ToolType, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
})

import_table('BrushHairTypes.csv', BrushHairType, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
})

# 3. Tables with FK to simple lookups
import_table('BrandModels.csv', BrandModel, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
    'BrandId': ('brand_id', null_or_val),
})

import_table('ToolShapes.csv', ToolShape, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
    'ToolTypeId': ('tool_type_id', null_or_val),
})

import_table('ToolSizes.csv', ToolSize, {
    'Id': ('id', null_or_val),
    'Size': ('size', lambda v: v or ''),
    'ToolTypeId': ('tool_type_id', null_or_val),
})

import_table('Pigments.csv', Pigment, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
    'ColorId': ('color_id', null_or_val),
})

# 4. Files
import_table('Files.csv', File, {
    'Id': ('id', null_or_val),
    'OriginalFileName': ('original_file_name', lambda v: v or ''),
    'UrlPath': ('url_path', lambda v: v or ''),
    'Type': ('type', lambda v: v or ''),
    'IsDeleted': ('is_deleted', null_or_bool),
})

# 5. Paints (FK to Brand, BrandModel, Color, Store, File)
import_table('Paints.csv', Paint, {
    'Id': ('id', null_or_val),
    'Name': ('name', lambda v: v or ''),
    'ImageId': ('image_id', null_or_val),
    'BrandId': ('brand_id', null_or_val),
    'BrandModelId': ('brand_model_id', null_or_val),
    'Type': ('type', lambda v: int(v) if v else 0),
    'ColorId': ('color_id', null_or_val),
    'RefPaint': ('ref_paint', lambda v: v or ''),
    'RefBrandColor': ('ref_brand_color', lambda v: v or ''),
    'Granulating': ('granulating', null_or_bool),
    'Staining': ('staining', null_or_bool),
    'Opacity': ('opacity', null_or_int),
    'OpacityNumber': ('opacity_number', null_or_int),
    'Quality': ('quality', null_or_int),
    'StoreId': ('store_id', null_or_val),
    'Price': ('price', null_or_decimal),
})

import_table('PigmentPaints.csv', PigmentPaint, {
    'Id': ('id', null_or_val),
    'PaintId': ('paint_id', null_or_val),
    'PigmentId': ('pigment_id', null_or_val),
})

# 6. Papers
import_table('Papers.csv', Paper, {
    'Id': ('id', null_or_val),
    'ColorId': ('color_id', null_or_val),
    'GSM': ('gsm', null_or_decimal),
    'BrandId': ('brand_id', null_or_val),
    'BrandModelId': ('brand_model_id', null_or_val),
    'Ref': ('ref', lambda v: v or ''),
    'OriginalSize': ('original_size', lambda v: v or ''),
    'PaperMaterialId': ('paper_material_id', null_or_val),
    'PaperSurfaceId': ('paper_surface_id', null_or_val),
    'StoreId': ('store_id', null_or_val),
    'ImageId': ('image_id', null_or_val),
    'Price': ('price', null_or_decimal),
    'VerboseName': ('verbose_name', lambda v: v or ''),
})

# 7. Tools
import_table('Tools.csv', Tool, {
    'Id': ('id', null_or_val),
    'BrandId': ('brand_id', null_or_val),
    'ModelId': ('model_id', null_or_val),
    'ShapeId': ('shape_id', null_or_val),
    'BrushHairTypeId': ('brush_hair_type_id', null_or_val),
    'ImageId': ('image_id', null_or_val),
    'TypeId': ('type_id', null_or_val),
    'SizeId': ('size_id', null_or_val),
    'StoreId': ('store_id', null_or_val),
    'Price': ('price', null_or_decimal),
    'Quality': ('quality', null_or_int),
})

# 8. Strokes (headerless CSV, commas in Description replaced with ;;)
stroke_cols = ['Id','Title','Description','Image600Id','PaperId','ImageUrl','OrderId','Tags','ImageOriginalId','Image100Id','Image1800Id','Image2500Id']
stroke_rows = []
with open(os.path.join(EXPORT_DIR, 'Strokes.csv'), 'r', encoding='utf-8', errors='replace') as f:
    import csv as csv2
    reader = csv2.reader(f)
    for row in reader:
        if len(row) != 12:
            continue
        d = dict(zip(stroke_cols, row))
        # Restore commas in description
        desc = (d.get('Description') or '').replace(';;', ',')
        if desc == 'NULL':
            desc = ''
        def nv(v):
            v = v.strip() if v else ''
            return v if v and v != 'NULL' and len(v) <= 36 else None

        def nv_url(v):
            v = v.strip() if v else ''
            return v if v and v != 'NULL' else ''

        stroke_rows.append(Stroke(
            id=d['Id'].strip() if d['Id'] and len(d['Id'].strip()) <= 36 else None,
            order_id=int(d['OrderId']) if d['OrderId'] and d['OrderId'] != 'NULL' and d['OrderId'].strip().isdigit() else 0,
            title=d['Title'] if d['Title'] != 'NULL' else '',
            description=desc,
            paper_id=nv(d['PaperId']),
            image_url=nv_url(d['ImageUrl']),
            tags=d['Tags'] if d['Tags'] and d['Tags'] != 'NULL' else '',
            image_100_id=nv(d['Image100Id']),
            image_600_id=nv(d['Image600Id']),
            image_1800_id=nv(d['Image1800Id']),
            image_2500_id=nv(d['Image2500Id']),
            image_original_id=nv(d['ImageOriginalId']),
        ))
Stroke.objects.bulk_create(stroke_rows, ignore_conflicts=True, batch_size=500)
print(f'  Strokes: {len(stroke_rows)} rows')

# 9. Junction tables
import_table('StrokePaints.csv', StrokePaint, {
    'Id': ('id', null_or_val),
    'StrokeId': ('stroke_id', null_or_val),
    'PaintId': ('paint_id', null_or_val),
})

import_table('StrokeTools.csv', StrokeTool, {
    'Id': ('id', null_or_val),
    'StrokeId': ('stroke_id', null_or_val),
    'ToolId': ('tool_id', null_or_val),
})

print('\nImport complete!')
