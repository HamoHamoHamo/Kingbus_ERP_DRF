import os
from config.settings.base import BASE_DIR
from firebase_admin import credentials, messaging, initialize_app, storage, _apps, get_app, delete_app
from my_settings import CRED_PATH, CLOUD_MEDIA_PATH
from config.custom_logging import logger

def send_message(title, body, token, topic):
    try:
        
        cred_path = os.path.join(BASE_DIR, CRED_PATH)
        cred = credentials.Certificate(cred_path)
        

        try:
            app = get_app()
            delete_app(app)
            initialize_app(cred)
        except ValueError:
            # Firebase app has not been initialized yet
            initialize_app(cred)

        # if not firebase_admin._apps:
        #     firebase_admin.initialize_app(cred)

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
    except Exception as e:
        print(f"Message Error : {e}")
        logger.error(f"Message Error : {e}")
        # raise Exception(f"Message Error : {e}")