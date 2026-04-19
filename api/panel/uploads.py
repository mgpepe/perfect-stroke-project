"""Panel-facing wrappers around FileService for R2 uploads."""

from typing import Optional

from api.models import File
from api.services.file_service import FileService


def upload_single_image(uploaded_file, *, path: str = '', file_type: str = '') -> File:
    """Upload one image (no resizing) and return the File row.

    Used for Paint/Paper/Tool where we only need one canonical image.
    """
    service = FileService()
    created = service.upload_files([uploaded_file], path=path, file_type=file_type)
    return created[0]


def upload_stroke_image_set(uploaded_file, *, path: str = 'stroke_photos', file_type: str = 'stroke') -> dict:
    """Upload a stroke image at all 5 sizes and return a dict of File rows.

    Keys: file_100, file_600, file_1800, file_2500, file_original.
    """
    service = FileService()
    sets = service.create_image_set([uploaded_file], path=path, file_type=file_type)
    return sets[0]


def attach_stroke_image_set(stroke, file_set: dict) -> None:
    """Apply an uploaded image set to a Stroke and save.

    Creates a new Image row owning the variants, links it as
    stroke.image, and also updates the legacy per-size FKs so the
    public API serializers (which still read them) stay in sync.
    """
    from api.models import Image

    image = Image.objects.create(
        size_100=file_set['file_100'],
        size_600=file_set['file_600'],
        size_1800=file_set['file_1800'],
        size_2500=file_set['file_2500'],
        size_original=file_set['file_original'],
    )
    stroke.image = image
    stroke.image_100 = file_set['file_100']
    stroke.image_600 = file_set['file_600']
    stroke.image_1800 = file_set['file_1800']
    stroke.image_2500 = file_set['file_2500']
    stroke.image_original = file_set['file_original']
    stroke.image_url = file_set['file_original'].url_path
    stroke.save()
