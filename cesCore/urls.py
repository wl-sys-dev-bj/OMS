"""
URL configuration for cesCore project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("frontend.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )

handler400 = "frontend.views.custom_bad_request"
handler403 = "frontend.views.custom_permission_denied"
handler404 = "frontend.views.custom_page_not_found"
handler500 = "frontend.views.custom_server_error"
