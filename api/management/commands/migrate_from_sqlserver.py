"""
Management command to migrate data from SQL Server to PostgreSQL.

Usage:
    python manage.py migrate_from_sqlserver --connection "Driver={ODBC Driver 17 for SQL Server};Server=...;Database=...;UID=...;PWD=..."

Or set SQLSERVER_CONNECTION_STRING in your .env file:
    python manage.py migrate_from_sqlserver
"""
import pyodbc
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from decouple import config

from api.models import (
    Brand, BrandModel, Color, File, Store, PaperMaterial, PaperSurface,
    ToolType, ToolShape, ToolSize, BrushHairType, Pigment, PigmentPaint,
    Paint, Paper, Tool, Stroke, StrokePaint, StrokeTool,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Migrate data from SQL Server to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--connection',
            type=str,
            default='',
            help='SQL Server connection string (or set SQLSERVER_CONNECTION_STRING in .env)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print counts without migrating',
        )

    def handle(self, *args, **options):
        conn_str = options['connection'] or config('SQLSERVER_CONNECTION_STRING', default='')
        if not conn_str:
            self.stderr.write('No connection string provided. Use --connection or set SQLSERVER_CONNECTION_STRING')
            return

        self.stdout.write(f'Connecting to SQL Server...')
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        if options['dry_run']:
            self._dry_run(cursor)
            conn.close()
            return

        self._migrate_users(cursor)
        self._migrate_simple_table(cursor, 'Brands', Brand, {'Id': 'id', 'Name': 'name'})
        self._migrate_simple_table(cursor, 'Colors', Color, {'Id': 'id', 'Name': 'name', 'HexCode': 'hex_code'})
        self._migrate_simple_table(cursor, 'Stores', Store, {'Id': 'id', 'Name': 'name', 'Url': 'url'})
        self._migrate_simple_table(cursor, 'PaperMaterials', PaperMaterial, {'Id': 'id', 'Name': 'name'})
        self._migrate_simple_table(cursor, 'PaperSurfaces', PaperSurface, {'Id': 'id', 'Name': 'name'})
        self._migrate_simple_table(cursor, 'ToolTypes', ToolType, {'Id': 'id', 'Name': 'name'})
        self._migrate_simple_table(cursor, 'BrushHairTypes', BrushHairType, {'Id': 'id', 'Name': 'name'})
        self._migrate_brand_models(cursor)
        self._migrate_tool_shapes(cursor)
        self._migrate_tool_sizes(cursor)
        self._migrate_files(cursor)
        self._migrate_pigments(cursor)
        self._migrate_paints(cursor)
        self._migrate_pigment_paints(cursor)
        self._migrate_papers(cursor)
        self._migrate_tools(cursor)
        self._migrate_strokes(cursor)
        self._migrate_stroke_paints(cursor)
        self._migrate_stroke_tools(cursor)

        conn.close()
        self.stdout.write(self.style.SUCCESS('Migration completed successfully!'))

    def _dry_run(self, cursor):
        tables = [
            'AspNetUsers', 'Brands', 'BrandModels', 'Colors', 'Stores',
            'PaperMaterials', 'PaperSurfaces', 'ToolTypes', 'ToolShapes',
            'ToolSizes', 'BrushHairTypes', 'Files', 'Pigments', 'Paints',
            'PigmentPaints', 'Papers', 'Tools', 'Strokes', 'StrokePaints', 'StrokeTools',
        ]
        for table in tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM [{table}]')
                count = cursor.fetchone()[0]
                self.stdout.write(f'  {table}: {count} rows')
            except pyodbc.Error as e:
                self.stdout.write(f'  {table}: ERROR - {e}')

    def _get_rows(self, cursor, query):
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _migrate_simple_table(self, cursor, sql_table, model, field_map):
        self.stdout.write(f'Migrating {sql_table}...')
        rows = self._get_rows(cursor, f'SELECT * FROM [{sql_table}]')
        objs = []
        for row in rows:
            kwargs = {}
            for sql_col, django_field in field_map.items():
                kwargs[django_field] = row.get(sql_col) or ''
            objs.append(model(**kwargs))
        model.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} {sql_table}')

    def _migrate_users(self, cursor):
        self.stdout.write('Migrating Users...')
        rows = self._get_rows(cursor, 'SELECT * FROM [AspNetUsers]')
        for row in rows:
            if User.objects.filter(username=row['UserName']).exists():
                continue
            user = User(
                username=row['UserName'],
                email=row.get('Email') or '',
                first_name=row.get('FirstName') or '',
                last_name=row.get('LastName') or '',
                picture_url=row.get('PictureUrl') or '',
                website=row.get('Website') or '',
                bio=row.get('Bio') or '',
                facebook_id=row.get('FacbookId'),
            )
            if row.get('Birthday'):
                user.birthday = row['Birthday']
            user.set_unusable_password()
            user.save()
        self.stdout.write(f'  -> {len(rows)} users')

    def _migrate_brand_models(self, cursor):
        self.stdout.write('Migrating BrandModels...')
        rows = self._get_rows(cursor, 'SELECT * FROM [BrandModels]')
        objs = [BrandModel(id=r['Id'], name=r['Name'], brand_id=r['BrandId']) for r in rows]
        BrandModel.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} brand models')

    def _migrate_tool_shapes(self, cursor):
        self.stdout.write('Migrating ToolShapes...')
        rows = self._get_rows(cursor, 'SELECT * FROM [ToolShapes]')
        objs = [ToolShape(id=r['Id'], name=r['Name'], tool_type_id=r['ToolTypeId']) for r in rows]
        ToolShape.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} tool shapes')

    def _migrate_tool_sizes(self, cursor):
        self.stdout.write('Migrating ToolSizes...')
        rows = self._get_rows(cursor, 'SELECT * FROM [ToolSizes]')
        objs = [ToolSize(id=r['Id'], size=r['Size'], tool_type_id=r['ToolTypeId']) for r in rows]
        ToolSize.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} tool sizes')

    def _migrate_files(self, cursor):
        self.stdout.write('Migrating Files...')
        rows = self._get_rows(cursor, 'SELECT * FROM [Files]')
        objs = []
        for r in rows:
            objs.append(File(
                id=r['Id'],
                original_file_name=r.get('OriginalFileName') or '',
                url_path=r.get('UrlPath') or '',
                type=r.get('Type') or '',
                is_deleted=r.get('IsDeleted', False),
            ))
        File.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} files')

    def _migrate_pigments(self, cursor):
        self.stdout.write('Migrating Pigments...')
        rows = self._get_rows(cursor, 'SELECT * FROM [Pigments]')
        objs = [Pigment(id=r['Id'], name=r['Name'], color_id=r['ColorId']) for r in rows]
        Pigment.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} pigments')

    def _migrate_paints(self, cursor):
        self.stdout.write('Migrating Paints...')
        rows = self._get_rows(cursor, 'SELECT * FROM [Paints]')
        objs = []
        for r in rows:
            objs.append(Paint(
                id=r['Id'],
                name=r.get('Name') or '',
                image_id=r.get('ImageId'),
                brand_id=r.get('BrandId'),
                brand_model_id=r.get('BrandModelId'),
                type=r.get('Type', 0),
                color_id=r.get('ColorId'),
                ref_paint=r.get('RefPaint') or '',
                ref_brand_color=r.get('RefBrandColor') or '',
                granulating=r.get('Granulating'),
                staining=r.get('Staining'),
                opacity=r.get('Opacity'),
                opacity_number=r.get('OpacityNumber'),
                quality=r.get('Quality'),
                store_id=r.get('StoreId'),
                price=r.get('Price'),
            ))
        Paint.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} paints')

    def _migrate_pigment_paints(self, cursor):
        self.stdout.write('Migrating PigmentPaints...')
        rows = self._get_rows(cursor, 'SELECT * FROM [PigmentPaints]')
        objs = [PigmentPaint(id=r['Id'], paint_id=r['PaintId'], pigment_id=r['PigmentId']) for r in rows]
        PigmentPaint.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} pigment-paint links')

    def _migrate_papers(self, cursor):
        self.stdout.write('Migrating Papers...')
        rows = self._get_rows(cursor, 'SELECT * FROM [Papers]')
        objs = []
        for r in rows:
            objs.append(Paper(
                id=r['Id'],
                color_id=r.get('ColorId'),
                gsm=r.get('GSM'),
                brand_id=r.get('BrandId'),
                brand_model_id=r.get('BrandModelId'),
                ref=r.get('Ref') or '',
                original_size=r.get('OriginalSize') or '',
                paper_material_id=r.get('PaperMaterialId'),
                paper_surface_id=r.get('PaperSurfaceId'),
                store_id=r.get('StoreId'),
                image_id=r.get('ImageId'),
                price=r.get('Price'),
                verbose_name=r.get('VerboseName') or '',
            ))
        Paper.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} papers')

    def _migrate_tools(self, cursor):
        self.stdout.write('Migrating Tools...')
        rows = self._get_rows(cursor, 'SELECT * FROM [Tools]')
        objs = []
        for r in rows:
            objs.append(Tool(
                id=r['Id'],
                brand_id=r.get('BrandId'),
                model_id=r.get('ModelId'),
                shape_id=r.get('ShapeId'),
                brush_hair_type_id=r.get('BrushHairTypeId'),
                image_id=r.get('ImageId'),
                type_id=r.get('TypeId'),
                size_id=r.get('SizeId'),
                store_id=r.get('StoreId'),
                price=r.get('Price'),
                quality=r.get('Quality'),
            ))
        Tool.objects.bulk_create(objs, ignore_conflicts=True)
        self.stdout.write(f'  -> {len(objs)} tools')

    def _migrate_strokes(self, cursor):
        self.stdout.write('Migrating Strokes...')
        rows = self._get_rows(cursor, 'SELECT * FROM [Strokes]')
        objs = []
        for r in rows:
            objs.append(Stroke(
                id=r['Id'],
                order_id=r.get('OrderId', 0),
                title=r.get('Title') or '',
                description=r.get('Description') or '',
                paper_id=r.get('PaperId'),
                image_url=r.get('ImageUrl') or '',
                tags=r.get('Tags') or '',
                image_100_id=r.get('Image100Id'),
                image_600_id=r.get('Image600Id'),
                image_1800_id=r.get('Image1800Id'),
                image_2500_id=r.get('Image2500Id'),
                image_original_id=r.get('ImageOriginalId'),
            ))
        Stroke.objects.bulk_create(objs, ignore_conflicts=True, batch_size=1000)
        self.stdout.write(f'  -> {len(objs)} strokes')

    def _migrate_stroke_paints(self, cursor):
        self.stdout.write('Migrating StrokePaints...')
        rows = self._get_rows(cursor, 'SELECT * FROM [StrokePaints]')
        objs = [StrokePaint(id=r['Id'], stroke_id=r['StrokeId'], paint_id=r['PaintId']) for r in rows]
        StrokePaint.objects.bulk_create(objs, ignore_conflicts=True, batch_size=1000)
        self.stdout.write(f'  -> {len(objs)} stroke-paint links')

    def _migrate_stroke_tools(self, cursor):
        self.stdout.write('Migrating StrokeTools...')
        rows = self._get_rows(cursor, 'SELECT * FROM [StrokeTools]')
        objs = [StrokeTool(id=r['Id'], stroke_id=r['StrokeId'], tool_id=r['ToolId']) for r in rows]
        StrokeTool.objects.bulk_create(objs, ignore_conflicts=True, batch_size=1000)
        self.stdout.write(f'  -> {len(objs)} stroke-tool links')
