from django.contrib import admin
from .models import (
    Brand, BrandModel, Color, File, Store, PaperMaterial, PaperSurface,
    ToolType, ToolShape, ToolSize, BrushHairType, Pigment, PigmentPaint,
    Paint, Paper, Tool, Stroke, StrokePaint, StrokeTool,
)

admin.site.register(Brand)
admin.site.register(BrandModel)
admin.site.register(Color)
admin.site.register(File)
admin.site.register(Store)
admin.site.register(PaperMaterial)
admin.site.register(PaperSurface)
admin.site.register(ToolType)
admin.site.register(ToolShape)
admin.site.register(ToolSize)
admin.site.register(BrushHairType)
admin.site.register(Pigment)
admin.site.register(PigmentPaint)
admin.site.register(Paint)
admin.site.register(Paper)
admin.site.register(Tool)
admin.site.register(Stroke)
admin.site.register(StrokePaint)
admin.site.register(StrokeTool)
