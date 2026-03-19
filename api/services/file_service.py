import uuid
from io import BytesIO

import boto3
from botocore.config import Config
from PIL import Image
from django.conf import settings

from api.models import File


class FileService:
    SIZES = {
        'file_100': 100,
        'file_600': 600,
        'file_1800': 1800,
        'file_2500': 2500,
    }

    def __init__(self):
        self.s3 = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT_URL,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(region_name='auto', signature_version='s3v4'),
        )
        self.bucket = settings.R2_BUCKET_NAME
        self.public_url = settings.R2_PUBLIC_URL.rstrip('/')

    def _upload(self, file_bytes, key, content_type='image/jpeg'):
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        return f'{self.public_url}/{key}'

    def upload_files(self, files, path='', file_type=''):
        created = []
        for f in files:
            unique_name = f'{uuid.uuid4()}-{f.name}'
            key = f'{path}/{unique_name}' if path else unique_name
            url = self._upload(f.read(), key, f.content_type)

            db_file = File.objects.create(
                original_file_name=f.name,
                url_path=url,
                type=file_type,
            )
            created.append(db_file)
        return created

    def _resize_image(self, image_bytes, width):
        img = Image.open(BytesIO(image_bytes))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        ratio = width / img.width
        new_height = int(img.height * ratio)
        if width < img.width:
            img = img.resize((width, new_height), Image.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=90)
        buffer.seek(0)
        return buffer.getvalue()

    def create_image_set(self, files, path='', file_type=''):
        results = []
        for f in files:
            original_bytes = f.read()
            file_set = {}

            for size_key, width in self.SIZES.items():
                resized = self._resize_image(original_bytes, width)
                unique_name = f'{uuid.uuid4()}-{f.name}'
                key = f'{path}/{width}/{unique_name}' if path else f'{width}/{unique_name}'
                url = self._upload(resized, key)

                db_file = File.objects.create(
                    original_file_name=f.name,
                    url_path=url,
                    type=file_type,
                )
                file_set[size_key] = db_file

            unique_name = f'{uuid.uuid4()}-{f.name}'
            key = f'{path}/original/{unique_name}' if path else f'original/{unique_name}'
            url = self._upload(original_bytes, key, f.content_type)

            db_file = File.objects.create(
                original_file_name=f.name,
                url_path=url,
                type=file_type,
            )
            file_set['file_original'] = db_file

            results.append(file_set)
        return results
