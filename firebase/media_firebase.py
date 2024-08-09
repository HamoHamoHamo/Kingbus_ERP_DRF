from datetime import datetime, timedelta
from pathlib import Path
from firebase_admin import credentials, initialize_app, storage, _apps, get_app, delete_app
import os
from trp_drf.settings import BASE_DIR
from my_settings import CRED_PATH, STORAGE_BUCKET, CLOUD_MEDIA_PATH
from firebase.firebase import init_firebase

def upload_to_firebase(file, file_path):
    init_firebase(os.path.join(BASE_DIR, CRED_PATH))
    bucket = storage.bucket()
    blob = bucket.blob(file_path)
    blob.upload_from_filename(file.file.path)

    return

def get_download_url(path):
    init_firebase(os.path.join(BASE_DIR, CRED_PATH))
    # Firebase Storage에서 다운로드 링크 가져오기
    bucket = storage.bucket()
    blob = bucket.blob(path)
    
    # 만료 시간 설정 (예: 1시간)
    expiration = datetime.now() + timedelta(hours=1)
    url = blob.generate_signed_url(expiration)

    return url

def delete_firebase_file(path):
    init_firebase(os.path.join(BASE_DIR, CRED_PATH))
    try:
        bucket = storage.bucket()
        blob = bucket.blob(path)
        blob.delete()
        print(f"File {path} deleted successfully.")
        return True
    except Exception as e:
        print(f"File delete fail\nError: {e}" )
        return False