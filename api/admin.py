from django.contrib import admin
from .models import (
    Brand, BrandModel, Color, File, Store, PaperMaterial, PaperSurface,
    ToolType, ToolShape, ToolSize, BrushHairType, Pigment, PigmentPaint,
    Paint, Paper, Tool, Stroke, StrokePaint, StrokeTool, Device,
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


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'desired_git_ref', 'last_reported_ref',
        'last_status', 'last_heartbeat_at',
    )
    list_filter = ('last_status',)
    search_fields = ('id', 'name')
    readonly_fields = (
        'token', 'last_reported_ref', 'last_status', 'last_error',
        'last_heartbeat_at', 'last_update_at', 'created_at', 'updated_at',
    )
    fieldsets = (
        (None, {'fields': ('id', 'name', 'desired_git_ref', 'token')}),
        ('Last heartbeat', {
            'fields': (
                'last_reported_ref', 'last_status', 'last_error',
                'last_heartbeat_at', 'last_update_at',
            ),
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
