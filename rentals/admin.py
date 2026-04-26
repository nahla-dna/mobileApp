from django.contrib import admin
from .models import Villa, Booking, ContactMessage, Review

@admin.register(Villa)
class VillaAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "name", "location", "price_per_night", "featured")
    search_fields = ("reference_number", "name", "location")
    list_filter = ("featured", "location")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("villa", "guest_name", "guest_email", "start_date", "end_date", "created_at")
    search_fields = ("guest_name", "guest_email")
    list_filter = ("start_date", "end_date")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "created_at", "responded")
    list_filter = ("responded",)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("villa", "user", "rating", "created_at")
    search_fields = ("comment", "user__username")
    list_filter = ("rating",)
