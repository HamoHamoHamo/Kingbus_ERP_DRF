import os
from my_settings import CLOUD_MEDIA_PATH
from django.core.files.storage import FileSystemStorage
from media_firebase import upload_to_firebase
from django.db import models

def upload_files(files, tmp_path, model:models.Model):
    uploaded_paths = list()
    for file in files:
        # if file:
        tmp_file = FileSystemStorage(location=tmp_path).save('temp', file)
        tmp_filepath = os.path.join(tmp_path, tmp_file)
        try:
            upload_file_path = f'{CLOUD_MEDIA_PATH}{model.get_file_path()}_{file}'
            print(upload_file_path)
            upload_to_firebase(tmp_filepath, upload_file_path)
            uploaded_paths.append(upload_file_path)
            os.remove(tmp_filepath)
            
        except Exception as e:
            print("Firebase upload error", e)
            #파이어베이스 업로드 실패 시 파일 삭제
            os.remove(tmp_filepath)
            # file.delete()
        
    return uploaded_paths