import os
import firebase_admin
from config.settings import BASE_DIR
from firebase_admin import credentials, messaging
from my_settings import CRED_PATH, CLOUD_MEDIA_PATH

def send_message(title, body, token, topic):
    cred_path = os.path.join(BASE_DIR, CRED_PATH)
    cred = credentials.Certificate(cred_path)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    # Android 알림 설정
    android_config = messaging.AndroidConfig(
        notification=messaging.AndroidNotification(
            title=title,
            body=body,
            sound='kingbus.wav',  # 알림 소리 지정
            channel_id='DefaultChannel',
        )
    )

    
    # APNs 알림 설정
    apns_config = messaging.APNSConfig(
        payload=messaging.APNSPayload(
            aps=messaging.Aps(
                alert=messaging.ApsAlert(
                    title=title,
                    body=body,
                ),
                sound='KingbusAlarmSound.caf'  # 알림 소리 지정
            )
        )
    )
    message = messaging.Message(
        # android=android_config,
        apns=apns_config,
        token=token,
        topic=topic,
        data = {
            'title' : title,
            'body' : body,
            'sound' : 'kingbus.wav',  # 알림 소리 지정
        }
    )

    response = messaging.send(message)
    print('Successfully sent message:', response)
