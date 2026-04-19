"""Resolve stroke image URLs with fallback through FK → image_url → r2_image_map.

The legacy photo import populated r2_image_map.json (a static lookup
keyed by stroke id) instead of File rows. Panel screens need both
paths to work so imported strokes still show thumbnails.
"""
import json
import os
from functools import lru_cache

from django.conf import settings


@lru_cache(maxsize=1)
def _r2_map() -> dict:
    path = os.path.join(settings.BASE_DIR, 'r2_image_map.json')
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def r2_base() -> str:
    return (settings.R2_PUBLIC_URL or '').rstrip('/')


def absolute_url(value: str) -> str:
    """Prefix R2 public URL when a File.url_path holds a relative key.

    Older imports wrote `url_path='stroke-images/1800/…jpg'` (the R2
    object key) instead of a full URL, so the browser resolved the
    <img src> against the current page path. Normalize here.
    """
    if not value:
        return ''
    if value.startswith(('http://', 'https://', '//', 'data:')):
        return value
    base = r2_base()
    if not base:
        return value
    return f'{base}/{value.lstrip("/")}'


def stroke_url(stroke, size: str) -> str:
    """Best-effort URL for a stroke at a given size.

    size: '100' | '600' | '1800' | '2500' | 'original'
    Order of precedence:
        1. r2_image_map.json entry (authoritative for legacy imports —
           many File FKs point at nonexistent keys).
        2. File FK on the Stroke (image_{size}) for rows uploaded via
           the new panel flow.
        3. stroke.image_url (full URL column) — only for 'original'.
        4. '' if nothing is known.
    """
    paths = _r2_map().get(stroke.id)
    if paths and size in paths:
        return absolute_url(paths[size])

    fk_attr = f'image_{size}'
    fk = getattr(stroke, fk_attr, None)
    if fk and getattr(fk, 'url_path', ''):
        return absolute_url(fk.url_path)

    if size == 'original' and getattr(stroke, 'image_url', ''):
        return absolute_url(stroke.image_url)

    return ''


def annotate_strokes(strokes, sizes=('600',)):
    """Attach .thumb_url (default 600) to each stroke for template use.

    Pass extra sizes to set .thumb_{size}_url attributes.
    """
    for s in strokes:
        for size in sizes:
            url = stroke_url(s, size)
            attr = 'thumb_url' if size == '600' else f'thumb_{size}_url'
            setattr(s, attr, url)
    return strokes
