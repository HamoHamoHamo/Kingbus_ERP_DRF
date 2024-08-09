from django.apps import AppConfig


class DispatchConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dispatch'

    def ready(self): # ready메소드 추가
    	import dispatch.signals
