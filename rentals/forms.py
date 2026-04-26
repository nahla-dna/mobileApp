from django import forms
from .models import Villa
from .models import Booking
from .models import Review, ContactMessage
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User



class VillaForm(forms.ModelForm):
    class Meta:
        model = Villa
        fields = [
            'reference_number',
            'name',
            'description',
            'location',
            'price_per_night',
            'number_of_rooms',
            'max_guests',
            'main_image',
            'featured',
        ]


from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['guest_name', 'guest_email', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]

        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your Name"}),
            "email": forms.EmailInput(attrs={"placeholder": "Your Email"}),
            "message": forms.Textarea(attrs={"placeholder": "Your Question", "rows": 4}),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required.')

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


from django.core.exceptions import ValidationError
from datetime import date

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['guest_name', 'guest_email', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")

        if start and end:
            if start < date.today():
                raise ValidationError("Start date cannot be in the past.")
            if end <= start:
                raise ValidationError("End date must be after start date.")

        return cleaned_data