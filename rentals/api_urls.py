from django.urls import path
from .views import (
    VillaViewSet,
    BookingViewSet,
    ReviewViewSet,
    login_user,
    my_bookings,
    create_booking,
    contact_api,
)

villa_list = VillaViewSet.as_view({
    'get': 'list'
})

booking_list = BookingViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

review_list = ReviewViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

urlpatterns = [
    path('villas/', villa_list),
    path('bookings/', booking_list),
    path('reviews/', review_list),

    # 🔥 CUSTOM APIs
    path('login/', login_user),
    path('mybookings/', my_bookings),
    path('create-booking/', create_booking),
    path("contact/", contact_api),
]