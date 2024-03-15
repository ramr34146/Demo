from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    path('admin_td/', admin.site.urls),

    path('', include('allauth.urls')),
    path('dashboard/', include('dashboard.urls', namespace='auth')),
    path('', include('users.urls', namespace='users')),
    path('', include('core.urls', namespace='core')),

    path('api/', include('api.urls', namespace='api')),

    path('robots.txt', TemplateView.as_view(template_name="pages/robots.txt", content_type='text/plain')),
]


handler404 = "contact.views.error_404"
handler500 = "contact.views.error_500"

admin.site.site_header = "LeadsProject"
admin.site.site_title = f"LeadsProject Admin Portal"
admin.site.index_title = f"Welcome to LeadsProject"


if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

