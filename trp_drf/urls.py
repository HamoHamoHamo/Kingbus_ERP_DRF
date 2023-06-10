from django.contrib import admin
from django.urls import include, path
from humanresource import urls as userurls
from dispatch import urls as dispatch_urls
from complaint import urls as complaint_urls
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin', admin.site.urls),
    path('', include(userurls)),
    path('dispatch/', include(dispatch_urls)),
    path('complaint/', include(complaint_urls)),
    path('vehicle', include('vehicle.urls')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)