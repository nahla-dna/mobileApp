from django.contrib import admin
from django.urls import path, include

from rest_framework.routers import DefaultRouter
from rentals.views import VillaViewSet, BookingViewSet, ReviewViewSet, login_user


from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'villas', VillaViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),

    # website
    path('', include('rentals.urls')),

    # API
    path('login/', login_user),
    path('api/', include(router.urls)),
    path('api/', include('rentals.api_urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)