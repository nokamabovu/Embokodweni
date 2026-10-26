from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "Embokodweni Lifestyle admin"
admin.site.site_title = "Embokodweni admin"
admin.site.index_title = "Manage the website"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", include("core.dash_urls")),
    path("", include("core.urls")),
    # Serve uploaded gallery photos (small site, so Django serves them directly)
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
