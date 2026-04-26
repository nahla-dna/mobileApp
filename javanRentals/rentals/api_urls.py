from django.urls import path
from .views import (
    VillaViewSet,
    BookingViewSet,
    ReviewViewSet,
    login_user,
    register_view,
    my_bookings,
    create_booking,
    contact_api,
)
from .views import villas_nearby

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

    #  CUSTOM APIs
    path('login/', login_user),
    path("register/", register_view, name="register"),
    path('mybookings/', my_bookings),
    path('create-booking/', create_booking),
    path("contact/", contact_api),
    path('villas/nearby/', villas_nearby, name='villas-nearby'),
]