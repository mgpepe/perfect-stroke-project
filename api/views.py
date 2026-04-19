import json
import os
import random

from django.conf import settings
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes

from .models import (
    Brand, BrandModel, Color, File, Store, PaperMaterial, PaperSurface,
    ToolType, ToolShape, ToolSize, BrushHairType, Pigment, PigmentPaint,
    Paint, Paper, Tool, Stroke, StrokePaint, StrokeTool, Device,
)
from .serializers import (
    BrandSerializer, BrandModelGetSerializer, BrandModelEditSerializer,
    ColorGetSerializer, ColorEditSerializer, FileSerializer,
    StoreGetSerializer, StoreEditSerializer,
    PaperMaterialGetSerializer, PaperMaterialEditSerializer,
    PaperSurfaceGetSerializer, PaperSurfaceEditSerializer,
    ToolTypeGetSerializer, ToolTypeEditSerializer,
    ToolShapeGetSerializer, ToolShapeEditSerializer,
    ToolSizeGetSerializer, ToolSizeEditSerializer,
    BrushHairTypeGetSerializer, BrushHairTypeEditSerializer,
    PigmentGetSerializer, PigmentEditSerializer,
    PaintGetSerializer, PaintEditSerializer,
    PaperGetSerializer, PaperEditSerializer,
    ToolGetSerializer, ToolEditSerializer,
    StrokeGetMinSerializer, StrokeGetMaxSerializer,
    StrokeGetImageSerializer, StrokeGetImage1800Serializer,
    StrokeEditSerializer, StrokeBulkEditSerializer,
    StrokeFrontendSerializer, StrokeFrontendListSerializer,
)
from .pagination import RangePagination
from .filters import parse_filter_ids, parse_range_notation
from .services.file_service import FileService


def _load_r2_map():
    map_path = os.path.join(settings.BASE_DIR, 'r2_image_map.json')
    if os.path.exists(map_path):
        with open(map_path) as f:
            return json.load(f)
    return {}


# ─── Mixin for filter-by-ids pattern ─────────────────────────────

class FilterByIdsMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        ids = parse_filter_ids(self.request)
        if ids:
            qs = qs.filter(id__in=ids)
        return qs


# ─── Simple CRUD ViewSets ────────────────────────────────────────

class BrandViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]


class BrandModelViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = BrandModel.objects.select_related('brand').all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return BrandModelEditSerializer
        return BrandModelGetSerializer


class ColorViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = Color.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ColorEditSerializer
        return ColorGetSerializer


class StoreViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = Store.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return StoreEditSerializer
        return StoreGetSerializer


class PaperMaterialViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = PaperMaterial.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PaperMaterialEditSerializer
        return PaperMaterialGetSerializer


class PaperSurfaceViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = PaperSurface.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PaperSurfaceEditSerializer
        return PaperSurfaceGetSerializer


class ToolTypeViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = ToolType.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ToolTypeEditSerializer
        return ToolTypeGetSerializer


class ToolShapeViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = ToolShape.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ToolShapeEditSerializer
        return ToolShapeGetSerializer


class ToolSizeViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = ToolSize.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ToolSizeEditSerializer
        return ToolSizeGetSerializer


class BrushHairTypeViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = BrushHairType.objects.all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return BrushHairTypeEditSerializer
        return BrushHairTypeGetSerializer


class PigmentViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = Pigment.objects.select_related('color').all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PigmentEditSerializer
        return PigmentGetSerializer


# ─── Files ───────────────────────────────────────────────────────

class FileViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = File.objects.filter(is_deleted=False)
    serializer_class = FileSerializer

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        path = request.data.get('path', '')
        file_type = request.data.get('type', '')

        service = FileService()
        created_files = service.upload_files(files, path, file_type)

        serializer = FileSerializer(created_files, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Stroke Images ───────────────────────────────────────────────

class StrokeImageViewSet(viewsets.ViewSet):
    def list(self, request):
        ids = parse_filter_ids(request)
        qs = File.objects.filter(is_deleted=False)
        if ids:
            qs = qs.filter(id__in=ids)

        pagination = RangePagination()
        pagination.resource_name = 'files'
        page = pagination.paginate_queryset(qs, request)
        serializer = FileSerializer(page, many=True)
        return pagination.get_paginated_response(serializer.data)

    def create(self, request):
        stroke_id = request.data.get('stroke_id')
        files = request.FILES.getlist('files')
        path = request.data.get('path', '')
        file_type = request.data.get('type', '')

        service = FileService()
        file_sets = service.create_image_set(files, path, file_type)

        if stroke_id and file_sets:
            stroke = Stroke.objects.filter(id=stroke_id).first()
            if stroke:
                fs = file_sets[0]
                stroke.image_100 = fs['file_100']
                stroke.image_600 = fs['file_600']
                stroke.image_1800 = fs['file_1800']
                stroke.image_2500 = fs['file_2500']
                stroke.image_original = fs['file_original']
                stroke.save()

        return Response(file_sets, status=status.HTTP_201_CREATED)


# ─── Paints ──────────────────────────────────────────────────────

class PaintViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = Paint.objects.select_related(
        'brand', 'brand_model', 'color', 'store'
    ).prefetch_related('pigment_paints__pigment__color').all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PaintEditSerializer
        return PaintGetSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paginator = RangePagination()
        paginator.resource_name = 'paints'
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        PigmentPaint.objects.filter(paint=instance).delete()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Papers ──────────────────────────────────────────────────────

class PaperViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = Paper.objects.select_related(
        'color', 'brand', 'brand_model', 'paper_material', 'paper_surface'
    ).all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PaperEditSerializer
        return PaperGetSerializer


# ─── Tools ───────────────────────────────────────────────────────

class ToolViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ToolEditSerializer
        return ToolGetSerializer


# ─── Strokes ─────────────────────────────────────────────────────

class StrokeViewSet(FilterByIdsMixin, viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    queryset = Stroke.objects.prefetch_related(
        'stroke_paints__paint__brand',
        'stroke_paints__paint__brand_model',
        'stroke_paints__paint__color',
        'stroke_paints__paint__store',
        'stroke_paints__paint__pigment_paints__pigment__color',
        'stroke_tools',
    ).select_related(
        'paper__color', 'paper__brand', 'paper__brand_model',
        'paper__paper_surface',
        'image_100', 'image_600', 'image_1800', 'image_2500', 'image_original',
    ).all()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return StrokeEditSerializer
        if self.action == 'retrieve':
            return StrokeGetMinSerializer
        return StrokeGetMinSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # Sort support
        sort_param = request.query_params.get('sort')
        if sort_param:
            try:
                sort_field, sort_order = json.loads(sort_param)
                field_map = {'id': 'id', 'orderId': 'order_id', 'title': 'title'}
                django_field = field_map.get(sort_field, 'order_id')
                if sort_order == 'DESC':
                    django_field = f'-{django_field}'
                queryset = queryset.order_by(django_field)
            except (json.JSONDecodeError, ValueError):
                pass

        paginator = RangePagination()
        paginator.resource_name = 'strokes'
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        # Try by ID first, then by order_id
        try:
            order_id = int(pk)
            instance = Stroke.objects.filter(Q(id=pk) | Q(order_id=order_id)).first()
        except (ValueError, TypeError):
            instance = Stroke.objects.filter(id=pk).first()
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = StrokeGetMinSerializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='details')
    def details(self, request, pk=None):
        instance = self.get_object()
        serializer = StrokeGetMaxSerializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='get-images')
    def get_images(self, request):
        r2_map = _load_r2_map()
        stroke_ids_with_images = set(r2_map.keys())
        queryset = self.get_queryset().filter(id__in=stroke_ids_with_images)
        serializer = StrokeGetImageSerializer(queryset, many=True, context={'r2_map': r2_map})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='frontend/all')
    def frontend_list(self, request):
        """Returns strokes with images in the shape the frontend expects."""
        r2_map = _load_r2_map()
        r2_base = settings.R2_PUBLIC_URL.rstrip('/')
        # Only return strokes that have images on R2
        stroke_ids_with_images = set(r2_map.keys())
        queryset = self.get_queryset().filter(id__in=stroke_ids_with_images)
        serializer = StrokeFrontendListSerializer(
            queryset, many=True,
            context={'r2_map': r2_map, 'r2_base': r2_base},
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='frontend')
    def frontend_detail(self, request, pk=None):
        """Returns a single stroke by order_number in the shape the frontend expects."""
        r2_map = _load_r2_map()
        r2_base = settings.R2_PUBLIC_URL.rstrip('/')
        try:
            order_id = int(pk)
            instance = Stroke.objects.filter(order_id=order_id).first()
        except (ValueError, TypeError):
            instance = Stroke.objects.filter(id=pk).first()
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = StrokeFrontendSerializer(
            instance, context={'r2_map': r2_map, 'r2_base': r2_base},
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='get-random')
    def get_random(self, request):
        """Return a random stroke that has an image in R2.

        Query params:
          exclude: comma-separated stroke ids to exclude (used by display clients
                   to avoid recently-shown images).
        """
        exclude_raw = request.query_params.get('exclude', '')
        exclude_ids = {s.strip() for s in exclude_raw.split(',') if s.strip()}
        r2_map = _load_r2_map()
        r2_base = settings.R2_PUBLIC_URL.rstrip('/')
        candidate_ids = list(set(r2_map.keys()) - exclude_ids)
        if not candidate_ids:
            return Response(status=status.HTTP_404_NOT_FOUND)
        random_id = random.choice(candidate_ids)
        stroke = Stroke.objects.filter(id=random_id).first()
        if not stroke:
            return Response(status=status.HTTP_404_NOT_FOUND)
        paths = r2_map.get(random_id, {})
        path = paths.get('original') or paths.get('2500') or paths.get('1800') or paths.get('600')
        image_url = f'{r2_base}/{path.lstrip("/")}' if path else ''
        return Response({
            'id': str(stroke.id),
            'order_id': stroke.order_id,
            'image_url': image_url,
        })

    @action(detail=False, methods=['put'], url_path='bulk')
    def bulk_update(self, request):
        serializer = StrokeBulkEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        order_ids = parse_range_notation(data['strokes'])
        strokes = Stroke.objects.filter(order_id__in=order_ids)

        paint_ids = data.get('paint_ids', [])
        for stroke in strokes:
            for pid in paint_ids:
                StrokePaint.objects.get_or_create(stroke=stroke, paint_id=pid)

        remove_paint_ids = data.get('remove_paint_ids', [])
        if remove_paint_ids:
            StrokePaint.objects.filter(
                stroke__in=strokes, paint_id__in=remove_paint_ids
            ).delete()

        tool_ids = data.get('tool_ids', [])
        for stroke in strokes:
            for tid in tool_ids:
                StrokeTool.objects.get_or_create(stroke=stroke, tool_id=tid)

        paper_id = data.get('paper_id')
        if paper_id:
            strokes.update(paper_id=paper_id)

        return Response({'status': 'ok'})


# ─── Remote device poll/heartbeat endpoints ──────────────────────

def _authenticate_device(request, device_id):
    """Return (device, None) on success or (None, Response) on auth failure."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None, Response(
            {'detail': 'Missing Bearer token'}, status=status.HTTP_401_UNAUTHORIZED,
        )
    token = auth[len('Bearer '):].strip()
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        return None, Response(status=status.HTTP_404_NOT_FOUND)
    # constant-time compare
    import hmac
    if not hmac.compare_digest(token, device.token):
        return None, Response(
            {'detail': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED,
        )
    return device, None


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def device_config(request, device_id):
    device, err = _authenticate_device(request, device_id)
    if err is not None:
        return err
    return Response({
        'id': device.id,
        'desired_git_ref': device.desired_git_ref,
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def device_wifi(request, device_id):
    """Return the set of WiFi networks this device should know.

    The Pi polls this and writes a NetworkManager connection file for each
    entry. Higher `priority` wins when multiple networks are reachable.
    """
    device, err = _authenticate_device(request, device_id)
    if err is not None:
        return err
    networks = list(device.wifi_networks.order_by('-priority', 'ssid').values(
        'ssid', 'password', 'priority', 'country',
    ))
    return Response({'networks': networks})


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def device_heartbeat(request, device_id):
    device, err = _authenticate_device(request, device_id)
    if err is not None:
        return err
    reported_ref = (request.data.get('reported_ref') or '').strip()[:64]
    reported_status = (request.data.get('status') or 'unknown').strip()[:16]
    reported_error = (request.data.get('error') or '').strip()[:4000]
    valid_statuses = {c[0] for c in Device.STATUS_CHOICES}
    if reported_status not in valid_statuses:
        reported_status = 'unknown'
    now = timezone.now()
    fields = ['last_reported_ref', 'last_status', 'last_error', 'last_heartbeat_at']
    if reported_ref and reported_ref != device.last_reported_ref:
        device.last_update_at = now
        fields.append('last_update_at')
    device.last_reported_ref = reported_ref
    device.last_status = reported_status
    device.last_error = reported_error
    device.last_heartbeat_at = now
    device.save(update_fields=fields)
    return Response({'ok': True, 'desired_git_ref': device.desired_git_ref})
