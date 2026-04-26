from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('villas/', views.all_villas, name='all_villas'),
    path('featured/', views.featured_villas, name='featured_villas'),

    # ✅ SEARCH FIXED
    path('search/', views.search_villas, name='search'),

    path('filter/', views.filter_villas, name='filter'),

    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('info/', views.information, name='information'),

    path('mybookings/', views.my_bookings_page, name='my_bookings'),

    path('villa/<int:villa_id>/', views.villa_detail, name='villa_detail'),
    path('villa/<int:villa_id>/book/', views.book_villa, name='book_villa'),

    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),

    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),  # ✅ ADD THIS
    path('logout/', views.logout_user, name='logout'),
    path('faq/', views.faq, name='faq'),

    path('booking/<int:booking_id>/pay/', views.payment_page, name='payment_page'),
    path('payment/success/', views.payment_success, name='payment_success'),

]