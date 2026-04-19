"""R2 helpers for per-stroke voice interpretations.

Audio files live at `assets/paper-collection-sounds/<stroke_id>.wav`.
They are not tracked in the DB — the filename is the stroke id.
"""
import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings


SOUND_PREFIX = 'assets/paper-collection-sounds'


_cache = {'ids': None, 'at': 0.0}
_TTL = 60  # seconds


def _s3():
    return boto3.client(
        's3',
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(region_name='auto', signature_version='s3v4'),
    )


def sound_key(order_id: int) -> str:
    return f'{SOUND_PREFIX}/{order_id}.wav'


def sound_url(order_id: int) -> str:
    base = (settings.R2_PUBLIC_URL or '').rstrip('/')
    return f'{base}/{sound_key(order_id)}' if base else sound_key(order_id)


def sound_exists(order_id: int) -> bool:
    if not order_id:
        return False
    try:
        _s3().head_object(Bucket=settings.R2_BUCKET_NAME, Key=sound_key(order_id))
        return True
    except ClientError:
        return False


def upload_sound(uploaded_file, order_id: int) -> str:
    """Upload audio to R2 at the canonical per-stroke path. Returns public URL."""
    content_type = uploaded_file.content_type or 'audio/wav'
    _s3().put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=sound_key(order_id),
        Body=uploaded_file.read(),
        ContentType=content_type,
    )
    _cache['at'] = 0.0
    return sound_url(order_id)


def delete_sound(order_id: int) -> None:
    try:
        _s3().delete_object(Bucket=settings.R2_BUCKET_NAME, Key=sound_key(order_id))
    except ClientError:
        pass
    _cache['at'] = 0.0  # invalidate


def existing_sound_order_ids() -> set:
    """Cached set of order_ids for which a sound file exists on R2.

    One list_objects_v2 scan per TTL, beats 100 HEAD requests per list page.
    """
    now = time.time()
    if _cache['ids'] is not None and (now - _cache['at']) < _TTL:
        return _cache['ids']

    ids = set()
    try:
        s3 = _s3()
        token = None
        while True:
            kwargs = {'Bucket': settings.R2_BUCKET_NAME, 'Prefix': f'{SOUND_PREFIX}/'}
            if token:
                kwargs['ContinuationToken'] = token
            resp = s3.list_objects_v2(**kwargs)
            for obj in resp.get('Contents', []):
                name = obj['Key'].rsplit('/', 1)[-1]
                stem = name.rsplit('.', 1)[0]
                if stem.isdigit():
                    ids.add(int(stem))
            if not resp.get('IsTruncated'):
                break
            token = resp.get('NextContinuationToken')
    except ClientError:
        pass

    _cache['ids'] = ids
    _cache['at'] = now
    return ids


def invalidate_sound_cache() -> None:
    _cache['at'] = 0.0
