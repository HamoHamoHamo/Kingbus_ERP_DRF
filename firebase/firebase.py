from firebase_admin import credentials, initialize_app, storage, _apps, get_app, delete_app, firestore
import os
from trp_drf.settings import BASE_DIR
from my_settings import CRED_PATH, STORAGE_BUCKET, CLOUD_MEDIA_PATH


def is_correct_storage_bucket(app, expected_bucket):
    try:
        bucket = storage.bucket(app=app)
        return bucket.name == expected_bucket
    except Exception as e:
        return False

def init_firebase(dir):
    cred = credentials.Certificate(dir)
    if not _apps:
        initialize_app(cred, {
            'storageBucket': STORAGE_BUCKET,
        })

    try:
        app = get_app()
        if not is_correct_storage_bucket(app, STORAGE_BUCKET):
            delete_app(app)
            initialize_app(cred, {
                'storageBucket': STORAGE_BUCKET,
            })
    except ValueError:
        # Firebase app has not been initialized yet
        initialize_app(cred, {
            'storageBucket': STORAGE_BUCKET,
        })


