"""
Management command to seed the database with initial data.
Matches the .NET PerfectStrokeDbSeed.

Usage:
    python manage.py seed
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from api.models import (
    Brand, BrandModel, Color, Store, PaperMaterial, PaperSurface,
    ToolType, ToolShape, ToolSize, BrushHairType, Pigment,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with initial data'

    def handle(self, *args, **options):
        self._seed_user()
        self._seed_stores()
        self._seed_brush_hair_types()
        self._seed_tool_types()
        self._seed_colors()
        self._seed_brands()
        self._seed_paper_materials()
        self._seed_paper_surfaces()
        self._seed_pigments()
        self.stdout.write(self.style.SUCCESS('Seeding complete!'))

    def _create_if_not_exists(self, model, name_field='name', **kwargs):
        lookup = {name_field: kwargs[name_field]}
        obj, created = model.objects.get_or_create(defaults=kwargs, **lookup)
        return obj

    def _seed_user(self):
        if not User.objects.filter(email='p@hakomo.com').exists():
            User.objects.create_superuser(
                username='admin',
                email='p@hakomo.com',
                password='Pass@word1',
                first_name='Admin',
                last_name='User',
            )
            self.stdout.write('  Created default user')

    def _seed_stores(self):
        stores = [
            'Slanchogled', 'Amazon', "Jackson's Art", 'Schminke',
            'Winsor & Newton', 'Daniel Smith', 'Daler Rowney', 'Royal Talens',
        ]
        for name in stores:
            self._create_if_not_exists(Store, name=name)
        self.stdout.write(f'  Seeded {len(stores)} stores')

    def _seed_brush_hair_types(self):
        types = [
            'Kolinsky Sable', 'Red Sable', 'Squirrel', 'Goat',
            'Hog/Bristle', 'Synthetic', 'Ox Hair', 'Pony',
        ]
        for name in types:
            self._create_if_not_exists(BrushHairType, name=name)
        self.stdout.write(f'  Seeded {len(types)} brush hair types')

    def _seed_tool_types(self):
        brush = self._create_if_not_exists(ToolType, name='Brush')
        palette_knife = self._create_if_not_exists(ToolType, name='Palette Knife')
        pencil = self._create_if_not_exists(ToolType, name='Pencil')

        # Shapes
        shapes = ['Round', 'Flat', 'Filbert', 'Fan', 'Angular', 'Mop', 'Rigger', 'Dagger']
        for name in shapes:
            ToolShape.objects.get_or_create(name=name, defaults={'tool_type': brush})

        # Sizes
        sizes = ['0', '1', '2', '4', '6', '8', '10', '12', '14', '16', '20']
        for size in sizes:
            ToolSize.objects.get_or_create(size=size, defaults={'tool_type': brush})

        self.stdout.write('  Seeded tool types, shapes, and sizes')

    def _seed_colors(self):
        colors = [
            ('White', '#FFFFFF'), ('Black', '#000000'), ('Red', '#FF0000'),
            ('Blue', '#0000FF'), ('Yellow', '#FFFF00'), ('Green', '#008000'),
            ('Orange', '#FFA500'), ('Purple', '#800080'), ('Brown', '#8B4513'),
            ('Pink', '#FFC0CB'), ('Grey', '#808080'),
        ]
        for name, hex_code in colors:
            Color.objects.get_or_create(name=name, defaults={'hex_code': hex_code})
        self.stdout.write(f'  Seeded {len(colors)} colors')

    def _seed_brands(self):
        brands_and_models = {
            'Winsor & Newton': ['Cotman', 'Professional', 'Galeria'],
            'Daniel Smith': ['Extra Fine'],
            'Schmincke': ['Horadam', 'Akademie'],
            'Royal Talens': ['Van Gogh', 'Rembrandt'],
            'Daler Rowney': ['Aquafine', 'Artists'],
            'Sennelier': ["l'Aquarelle"],
            'Holbein': ['Artists Watercolor'],
        ]
        for brand_name, models in brands_and_models.items():
            brand = self._create_if_not_exists(Brand, name=brand_name)
            for model_name in models:
                BrandModel.objects.get_or_create(name=model_name, defaults={'brand': brand})
        self.stdout.write(f'  Seeded {len(brands_and_models)} brands with models')

    def _seed_paper_materials(self):
        materials = ['Cotton', 'Cellulose', 'Cotton/Cellulose Blend']
        for name in materials:
            self._create_if_not_exists(PaperMaterial, name=name)
        self.stdout.write(f'  Seeded {len(materials)} paper materials')

    def _seed_paper_surfaces(self):
        surfaces = ['Hot Pressed', 'Cold Pressed', 'Rough']
        for name in surfaces:
            self._create_if_not_exists(PaperSurface, name=name)
        self.stdout.write(f'  Seeded {len(surfaces)} paper surfaces')

    def _seed_pigments(self):
        # Get colors for pigment assignment
        colors = {c.name: c for c in Color.objects.all()}
        pigments = [
            ('PW6', 'White'), ('PBk7', 'Black'), ('PR108', 'Red'),
            ('PB29', 'Blue'), ('PY42', 'Yellow'), ('PG7', 'Green'),
            ('PO73', 'Orange'), ('PV19', 'Purple'), ('PBr7', 'Brown'),
            ('PR122', 'Pink'), ('PBk6', 'Grey'),
            ('PY150', 'Yellow'), ('PB15', 'Blue'), ('PR101', 'Red'),
            ('PG36', 'Green'), ('PV23', 'Purple'),
        ]
        for name, color_name in pigments:
            color = colors.get(color_name)
            if color:
                Pigment.objects.get_or_create(name=name, defaults={'color': color})
        self.stdout.write(f'  Seeded {len(pigments)} pigments')
