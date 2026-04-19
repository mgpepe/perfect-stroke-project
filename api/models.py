import secrets
import uuid
from django.conf import settings
from django.db import models


def generate_id():
    return str(uuid.uuid4())


def generate_device_token():
    return secrets.token_hex(32)


class Brand(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'brands'

    def __str__(self):
        return self.name


class BrandModel(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='models')

    class Meta:
        db_table = 'brand_models'

    def __str__(self):
        return self.name


class Color(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)
    hex_code = models.CharField(max_length=7, blank=True)

    class Meta:
        db_table = 'colors'

    def __str__(self):
        return self.name


class File(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    original_file_name = models.CharField(max_length=500)
    url_path = models.URLField(max_length=1000, blank=True)
    type = models.CharField(max_length=100, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    deleted_on = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'files'

    def __str__(self):
        return self.original_file_name


class Store(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)
    url = models.URLField(blank=True)

    class Meta:
        db_table = 'stores'

    def __str__(self):
        return self.name


class PaperMaterial(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'paper_materials'

    def __str__(self):
        return self.name


class PaperSurface(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'paper_surfaces'

    def __str__(self):
        return self.name


class ToolType(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'tool_types'

    def __str__(self):
        return self.name


class ToolShape(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)
    tool_type = models.ForeignKey(ToolType, on_delete=models.CASCADE, related_name='shapes')

    class Meta:
        db_table = 'tool_shapes'

    def __str__(self):
        return self.name


class ToolSize(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    size = models.CharField(max_length=50)
    tool_type = models.ForeignKey(ToolType, on_delete=models.CASCADE, related_name='sizes')

    class Meta:
        db_table = 'tool_sizes'

    def __str__(self):
        return self.size


class BrushHairType(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'brush_hair_types'

    def __str__(self):
        return self.name


class Pigment(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)
    color = models.ForeignKey(Color, on_delete=models.CASCADE, related_name='pigments')

    class Meta:
        db_table = 'pigments'

    def __str__(self):
        return self.name


class PaintType(models.IntegerChoices):
    ACRYLIC = 0, 'Acrylic'
    WATERCOLOR = 1, 'WaterColor'
    OIL = 2, 'Oil'
    GOUACHE = 3, 'Gouache'
    INK = 4, 'Ink'
    PASTEL = 5, 'Pastel'


class OpacityType(models.IntegerChoices):
    OPAQUE = 0, 'Opaque'
    SEMI_OPAQUE = 1, 'SemiOpaque'
    SEMI = 2, 'Semi'
    SEMI_TRANSPARENT = 3, 'SemiTransparent'
    TRANSPARENT = 4, 'Transparent'


class QualityGrade(models.IntegerChoices):
    ARTISTS_GRADE = 0, 'ArtistsGrade'
    STUDENT_GRADE = 1, 'StudentGrade'


class Paint(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    name = models.CharField(max_length=255)
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='paint_images')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='paints')
    brand_model = models.ForeignKey(BrandModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='paints')
    type = models.IntegerField(choices=PaintType.choices)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name='paints')
    ref_paint = models.CharField(max_length=255, blank=True)
    ref_brand_color = models.CharField(max_length=255, blank=True)
    granulating = models.BooleanField(null=True, blank=True)
    staining = models.BooleanField(null=True, blank=True)
    opacity = models.IntegerField(choices=OpacityType.choices, null=True, blank=True)
    opacity_number = models.IntegerField(null=True, blank=True)
    quality = models.IntegerField(choices=QualityGrade.choices, null=True, blank=True)
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='paints')
    price = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    pigments = models.ManyToManyField(Pigment, through='PigmentPaint', related_name='paints')

    class Meta:
        db_table = 'paints'

    def __str__(self):
        return self.name


class PigmentPaint(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    paint = models.ForeignKey(Paint, on_delete=models.CASCADE, related_name='pigment_paints')
    pigment = models.ForeignKey(Pigment, on_delete=models.CASCADE, related_name='pigment_paints')

    class Meta:
        db_table = 'pigment_paints'
        unique_together = ('paint', 'pigment')


class Paper(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    color = models.ForeignKey(Color, on_delete=models.SET_NULL, null=True, blank=True, related_name='papers')
    gsm = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='papers')
    brand_model = models.ForeignKey(BrandModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='papers')
    ref = models.CharField(max_length=255, blank=True)
    original_size = models.CharField(max_length=255, blank=True)
    paper_material = models.ForeignKey(PaperMaterial, on_delete=models.SET_NULL, null=True, blank=True, related_name='papers')
    paper_surface = models.ForeignKey(PaperSurface, on_delete=models.SET_NULL, null=True, blank=True, related_name='papers')
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='papers')
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='paper_images')
    price = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    verbose_name = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = 'papers'

    def __str__(self):
        return self.verbose_name or self.ref or str(self.id)


class Tool(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='tools')
    model = models.ForeignKey(BrandModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='tools')
    shape = models.ForeignKey(ToolShape, on_delete=models.SET_NULL, null=True, blank=True, related_name='tools')
    brush_hair_type = models.ForeignKey(BrushHairType, on_delete=models.SET_NULL, null=True, blank=True, related_name='tools')
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='tool_images')
    type = models.ForeignKey(ToolType, on_delete=models.SET_NULL, null=True, blank=True, related_name='tools')
    size = models.ForeignKey(ToolSize, on_delete=models.SET_NULL, null=True, blank=True, related_name='tools')
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='tools')
    price = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    quality = models.IntegerField(choices=QualityGrade.choices, null=True, blank=True)

    class Meta:
        db_table = 'tools'


class Stroke(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    order_id = models.IntegerField(default=0)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    paper = models.ForeignKey(Paper, on_delete=models.SET_NULL, null=True, blank=True, related_name='strokes')
    image_url = models.URLField(max_length=1000, blank=True)
    tags = models.CharField(max_length=500, blank=True)
    image_100 = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='stroke_img100')
    image_600 = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='stroke_img600')
    image_1800 = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='stroke_img1800')
    image_2500 = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='stroke_img2500')
    image_original = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name='stroke_imgoriginal')
    paints = models.ManyToManyField(Paint, through='StrokePaint', related_name='strokes')
    tools = models.ManyToManyField(Tool, through='StrokeTool', related_name='strokes')

    class Meta:
        db_table = 'strokes'
        ordering = ['order_id']

    def __str__(self):
        return self.title or f'Stroke #{self.order_id}'


class StrokePaint(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    stroke = models.ForeignKey(Stroke, on_delete=models.CASCADE, related_name='stroke_paints')
    paint = models.ForeignKey(Paint, on_delete=models.CASCADE, related_name='stroke_paints')

    class Meta:
        db_table = 'stroke_paints'


class StrokeTool(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    stroke = models.ForeignKey(Stroke, on_delete=models.CASCADE, related_name='stroke_tools')
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='stroke_tools')

    class Meta:
        db_table = 'stroke_tools'


class Device(models.Model):
    """A remote device (e.g. Raspberry Pi) polling for a desired code version.

    The server is the control plane for *which git ref should run*. App-level
    runtime config (tick interval, canvas size, ...) stays on the device.
    """

    STATUS_CHOICES = [
        ('ok', 'OK'),
        ('updating', 'Updating'),
        ('failed', 'Failed'),
        ('unknown', 'Unknown'),
    ]

    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=128, blank=True)
    token = models.CharField(max_length=64, default=generate_device_token, editable=False)
    desired_git_ref = models.CharField(max_length=64, default='main')
    last_reported_ref = models.CharField(max_length=64, blank=True)
    last_status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='unknown')
    last_error = models.TextField(blank=True)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    last_update_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devices'
        ordering = ['id']

    def __str__(self):
        return self.name or self.id


class WifiNetwork(models.Model):
    """A WiFi network known to a Device.

    The Pi polls /api/devices/<id>/wifi/ and writes a NetworkManager
    connection file for each row. Higher priority wins when multiple
    networks are in range.
    """

    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name='wifi_networks',
    )
    ssid = models.CharField(max_length=64)
    password = models.CharField(max_length=128, blank=True,
                                help_text='Leave empty for open networks.')
    priority = models.IntegerField(
        default=50,
        help_text='Higher wins when multiple networks are reachable (NM autoconnect-priority).',
    )
    country = models.CharField(max_length=2, default='BG',
                               help_text='Two-letter country code (regulatory domain).')
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wifi_networks'
        ordering = ['-priority', 'ssid']
        unique_together = ('device', 'ssid')

    def __str__(self):
        return f'{self.device_id}:{self.ssid}'


class ModifyJob(models.Model):
    """A natural-language modification request executed by an AI agent.

    The job owns a workspace (fresh clone of the target repo) and walks
    through: clone -> edit -> test -> (correct up to N rounds) -> commit ->
    push. All state is recorded here so the panel can show live progress.
    """

    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('testing', 'Testing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    PHASE_CHOICES = [
        ('', '—'),
        ('cloning', 'Cloning'),
        ('editing', 'Editing'),
        ('testing', 'Testing'),
        ('correcting', 'Correcting'),
        ('committing', 'Committing'),
        ('pushing', 'Pushing'),
    ]

    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    prompt = models.TextField()
    repo = models.CharField(max_length=200, default='mgpepe/perfect-stroke-project-epaper')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='queued')
    current_phase = models.CharField(max_length=16, choices=PHASE_CHOICES, blank=True, default='')
    round_num = models.IntegerField(default=0)
    max_rounds = models.IntegerField(default=10)
    cost_usd = models.FloatField(default=0.0)
    max_cost_usd = models.FloatField(default=200.0)
    model = models.CharField(max_length=64, default='claude-opus-4-7')
    commit_sha = models.CharField(max_length=64, blank=True, default='')
    branch = models.CharField(max_length=64, default='main')
    diff = models.TextField(blank=True, default='')
    error = models.TextField(blank=True, default='')
    log = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='modify_jobs',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'modify_jobs'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['-created_at']), models.Index(fields=['status'])]

    def __str__(self):
        return f'{self.id[:8]}: {self.prompt[:60]}'

    def append_log(self, line):
        from django.utils import timezone
        stamp = timezone.now().strftime('%H:%M:%S')
        self.log = (self.log or '') + f'[{stamp}] {line}\n'
        self.save(update_fields=['log', 'updated_at'])

    def is_terminal(self):
        return self.status in ('succeeded', 'failed', 'cancelled')


class Contact(models.Model):
    """A person (collector / buyer). One contact can hold many sales."""
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contacts'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        full = f'{self.first_name} {self.last_name}'.strip()
        return full or self.email or str(self.id)


class Sale(models.Model):
    """A single stroke purchase. OneToOne to Stroke — one sale per stroke."""
    id = models.CharField(max_length=36, primary_key=True, default=generate_id)
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT, related_name='sales')
    stroke = models.OneToOneField(Stroke, on_delete=models.CASCADE, related_name='sale')
    sold_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sales'
        ordering = ['-sold_at', '-created_at']

    def __str__(self):
        return f'{self.stroke_id} → {self.contact}'
