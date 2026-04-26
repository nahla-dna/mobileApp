from django.db import models
from django.contrib.auth.models import User

class Villa(models.Model):
    reference_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    price_per_night = models.DecimalField(max_digits=9, decimal_places=2)
    number_of_rooms = models.PositiveSmallIntegerField(default=1)
    max_guests = models.PositiveSmallIntegerField(default=1)
    main_image = models.ImageField(upload_to='villas/', null=True, blank=True)
    featured = models.BooleanField(default=False)   # for "Book Now" / featured section
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference_number} — {self.name}"

class Booking(models.Model):
    villa = models.ForeignKey(Villa, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    guest_name = models.CharField(max_length=200)
    guest_email = models.EmailField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    canceled = models.BooleanField(default=False)
    cancellation_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Booking {self.villa.reference_number} by {self.guest_email}"
    class Meta:
        ordering = ['-created_at']



class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)

    def __str__(self):
        return f"Contact from {self.name} <{self.email}>"
    


class Review(models.Model):
    villa = models.ForeignKey(Villa, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.villa.name} — {self.rating}★"

class Booking(models.Model):
    villa = models.ForeignKey(Villa, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    guest_name = models.CharField(max_length=200)
    guest_email = models.EmailField()
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    # NEW FIELDS
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)

    canceled = models.BooleanField(default=False)
    cancellation_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.villa.name} by {self.guest_email}"

    # CALCULATE PRICE
    def calculate_total(self):
        nights = (self.end_date - self.start_date).days
        return nights * self.villa.price_per_night