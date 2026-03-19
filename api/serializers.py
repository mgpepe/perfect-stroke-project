from rest_framework import serializers
from .models import (
    Brand, BrandModel, Color, File, Store, PaperMaterial, PaperSurface,
    ToolType, ToolShape, ToolSize, BrushHairType, Pigment, PigmentPaint,
    Paint, Paper, Tool, Stroke, StrokePaint, StrokeTool,
)


# ─── Simple lookups ──────────────────────────────────────────────

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']
        read_only_fields = ['id']


class BrandModelGetSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)

    class Meta:
        model = BrandModel
        fields = ['id', 'name', 'brand_id', 'brand']


class BrandModelEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandModel
        fields = ['name', 'brand_id']


class ColorGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name', 'hex_code']


class ColorEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['name', 'hex_code']


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'original_file_name', 'url_path', 'type']
        read_only_fields = ['id']


class StoreGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'name', 'url']


class StoreEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['name', 'url']


class PaperMaterialGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperMaterial
        fields = ['id', 'name']


class PaperMaterialEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperMaterial
        fields = ['name']


class PaperSurfaceGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperSurface
        fields = ['id', 'name']


class PaperSurfaceEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperSurface
        fields = ['name']


class ToolTypeGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolType
        fields = ['id', 'name']


class ToolTypeEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolType
        fields = ['name']


class ToolShapeGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolShape
        fields = ['id', 'name', 'tool_type_id']


class ToolShapeEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolShape
        fields = ['name', 'tool_type_id']


class ToolSizeGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolSize
        fields = ['id', 'size', 'tool_type_id']


class ToolSizeEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolSize
        fields = ['size', 'tool_type_id']


class BrushHairTypeGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrushHairType
        fields = ['id', 'name']


class BrushHairTypeEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrushHairType
        fields = ['name']


# ─── Pigment ─────────────────────────────────────────────────────

class PigmentGetSerializer(serializers.ModelSerializer):
    color = ColorGetSerializer(read_only=True)

    class Meta:
        model = Pigment
        fields = ['id', 'name', 'color_id', 'color']


class PigmentEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pigment
        fields = ['name', 'color_id']


class PigmentPaintGetSerializer(serializers.ModelSerializer):
    pigment = PigmentGetSerializer(read_only=True)

    class Meta:
        model = PigmentPaint
        fields = ['paint_id', 'pigment']


# ─── Paint ───────────────────────────────────────────────────────

class PaintGetSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    brand_model = BrandModelGetSerializer(read_only=True)
    color = ColorGetSerializer(read_only=True)
    store = StoreGetSerializer(read_only=True)
    pigment_paints = PigmentPaintGetSerializer(many=True, read_only=True)
    pigment_ids = serializers.SerializerMethodField()

    class Meta:
        model = Paint
        fields = [
            'id', 'name', 'image_id',
            'brand_id', 'brand', 'brand_model_id', 'brand_model',
            'type', 'color_id', 'color',
            'ref_paint', 'ref_brand_color',
            'granulating', 'staining', 'opacity', 'opacity_number', 'quality',
            'store_id', 'store', 'price',
            'pigment_paints', 'pigment_ids',
        ]

    def get_pigment_ids(self, obj):
        return list(obj.pigment_paints.values_list('pigment_id', flat=True))


class PaintEditSerializer(serializers.ModelSerializer):
    pigment_ids = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)

    class Meta:
        model = Paint
        fields = [
            'name', 'image_id', 'brand_id', 'brand_model_id',
            'type', 'color_id', 'ref_paint', 'ref_brand_color',
            'granulating', 'staining', 'opacity', 'opacity_number', 'quality',
            'store_id', 'price', 'pigment_ids',
        ]

    def create(self, validated_data):
        pigment_ids = validated_data.pop('pigment_ids', [])
        paint = super().create(validated_data)
        for pid in pigment_ids:
            PigmentPaint.objects.create(paint=paint, pigment_id=pid)
        return paint

    def update(self, instance, validated_data):
        pigment_ids = validated_data.pop('pigment_ids', None)
        paint = super().update(instance, validated_data)
        if pigment_ids is not None:
            PigmentPaint.objects.filter(paint=paint).delete()
            for pid in pigment_ids:
                PigmentPaint.objects.create(paint=paint, pigment_id=pid)
        return paint


# ─── Paper ───────────────────────────────────────────────────────

class PaperGetSerializer(serializers.ModelSerializer):
    verbose_name = serializers.SerializerMethodField()

    class Meta:
        model = Paper
        fields = [
            'id', 'color_id', 'gsm', 'brand_id', 'brand_model_id',
            'ref', 'original_size', 'paper_material_id', 'paper_surface_id',
            'store_id', 'image_id', 'price', 'verbose_name',
        ]

    def get_verbose_name(self, obj):
        parts = []
        if obj.gsm:
            parts.append(f'{obj.gsm}gsm')
        if obj.color:
            parts.append(obj.color.name)
        if obj.brand:
            parts.append(obj.brand.name)
        if obj.brand_model:
            parts.append(obj.brand_model.name)
        if obj.paper_surface:
            parts.append(obj.paper_surface.name)
        return ' '.join(parts) if parts else ''


class PaperEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paper
        fields = [
            'gsm', 'ref', 'original_size', 'price',
            'color_id', 'brand_id', 'brand_model_id',
            'paper_material_id', 'paper_surface_id', 'store_id', 'image_id',
        ]


# ─── Tool ────────────────────────────────────────────────────────

class ToolGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = [
            'id', 'brand_id', 'model_id', 'shape_id', 'brush_hair_type_id',
            'image_id', 'type_id', 'size_id', 'store_id', 'price', 'quality',
        ]


class ToolEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = [
            'price', 'quality', 'brand_id', 'model_id', 'shape_id',
            'brush_hair_type_id', 'image_id', 'type_id', 'size_id', 'store_id',
        ]


# ─── Stroke ──────────────────────────────────────────────────────

class StrokePaintGetSerializer(serializers.ModelSerializer):
    paint = PaintGetSerializer(read_only=True)

    class Meta:
        model = StrokePaint
        fields = ['id', 'paint']


class StrokeGetMinSerializer(serializers.ModelSerializer):
    paint_ids = serializers.SerializerMethodField()
    tool_ids = serializers.SerializerMethodField()

    class Meta:
        model = Stroke
        fields = [
            'id', 'order_id', 'title', 'description', 'paper_id',
            'paint_ids', 'tool_ids', 'image_url', 'tags',
            'image_100_id', 'image_600_id', 'image_1800_id',
            'image_2500_id', 'image_original_id',
        ]

    def get_paint_ids(self, obj):
        return list(obj.stroke_paints.values_list('paint_id', flat=True))

    def get_tool_ids(self, obj):
        return list(obj.stroke_tools.values_list('tool_id', flat=True))


class StrokeGetMaxSerializer(serializers.ModelSerializer):
    stroke_paints = StrokePaintGetSerializer(many=True, read_only=True)
    paper = PaperGetSerializer(read_only=True)

    class Meta:
        model = Stroke
        fields = [
            'id', 'order_id', 'title', 'description',
            'image_url', 'tags', 'stroke_paints', 'paper',
        ]


class StrokeGetImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Stroke
        fields = ['id', 'order_id', 'image_url']

    def get_image_url(self, obj):
        if obj.image_600:
            return obj.image_600.url_path
        return obj.image_url


class StrokeGetImage1800Serializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Stroke
        fields = ['id', 'order_id', 'image_url']

    def get_image_url(self, obj):
        if obj.image_1800:
            return obj.image_1800.url_path
        return obj.image_url


class StrokeEditSerializer(serializers.ModelSerializer):
    paint_ids = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)
    tool_ids = serializers.ListField(child=serializers.CharField(), required=False, write_only=True)

    class Meta:
        model = Stroke
        fields = [
            'order_id', 'title', 'description', 'paper_id',
            'image_url', 'tags',
            'image_100_id', 'image_600_id', 'image_1800_id',
            'image_2500_id', 'image_original_id',
            'paint_ids', 'tool_ids',
        ]

    def create(self, validated_data):
        paint_ids = validated_data.pop('paint_ids', [])
        tool_ids = validated_data.pop('tool_ids', [])
        stroke = super().create(validated_data)
        for pid in paint_ids:
            StrokePaint.objects.create(stroke=stroke, paint_id=pid)
        for tid in tool_ids:
            StrokeTool.objects.create(stroke=stroke, tool_id=tid)
        return stroke

    def update(self, instance, validated_data):
        paint_ids = validated_data.pop('paint_ids', None)
        tool_ids = validated_data.pop('tool_ids', None)
        stroke = super().update(instance, validated_data)
        if paint_ids is not None:
            StrokePaint.objects.filter(stroke=stroke).delete()
            for pid in paint_ids:
                StrokePaint.objects.create(stroke=stroke, paint_id=pid)
        if tool_ids is not None:
            StrokeTool.objects.filter(stroke=stroke).delete()
            for tid in tool_ids:
                StrokeTool.objects.create(stroke=stroke, tool_id=tid)
        return stroke


class StrokeBulkEditSerializer(serializers.Serializer):
    strokes = serializers.CharField(help_text='Comma/range notation e.g. "1-5,7,9-10"')
    paint_ids = serializers.ListField(child=serializers.CharField(), required=False)
    remove_paint_ids = serializers.ListField(child=serializers.CharField(), required=False)
    tool_ids = serializers.ListField(child=serializers.CharField(), required=False)
    paper_id = serializers.CharField(required=False, allow_blank=True)
