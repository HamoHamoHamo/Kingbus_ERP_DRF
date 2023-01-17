from django.contrib import admin
from django.urls import include, path
from humanresource import urls as userurls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(userurls)),
]
