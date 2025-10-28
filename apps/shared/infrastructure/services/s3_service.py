from threading import Lock

import boto3
from django.conf import settings


class S3Service:
    _instance = None
    _lock = Lock()  # making it thread safe, one instance for every thread

    def __new__(cls):
        # Thread-safe singleton initialization
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(S3Service, cls).__new__(cls)
                    cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self.client = boto3.client("s3")
        self.bucket_name = settings.AWS_S3_BUCKET_NAME

    def upload_file(self, file_path: str, key: str, content_type: str | None = None) -> str:
        extra_args = {"ContentType": content_type} if content_type else {}
        self.client.upload_file(file_path, self.bucket_name, key, ExtraArgs=extra_args)
        return self.get_file_url(key)

    def get_file_url(self, key: str) -> str:
        return f"{settings.AWS_S3_BASE_URL}/{key}"

    def generate_presigned_url(self, key: str, expiration: int = 3600, download: bool = False, filename: str | None = None) -> str:
        params = {'Bucket': self.bucket_name, 'Key': key}
        if download:
            download_filename = filename or key.split('/')[-1]
            params['ResponseContentDisposition'] = f'attachment; filename="{download_filename}"'

        url = self.client.generate_presigned_url('get_object', Params=params, ExpiresIn=expiration)
        return url
