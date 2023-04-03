from django.contrib import admin
from django.urls import include, path
from humanresource import urls as userurls
from dispatch import urls as dispatch_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(userurls)),
    path('dispatch/', include(dispatch_urls)),
]
