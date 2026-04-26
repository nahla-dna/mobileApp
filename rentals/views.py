from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime

from .models import Villa, Booking, Review, ContactMessage
from .forms import ContactForm, SignUpForm, BookingForm, ReviewForm

# DRF
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.models import User

from .serializers import VillaSerializer, ReviewSerializer, BookingSerializer


# ---------------- HOME ----------------

def home(request):
    featured = Villa.objects.filter(featured=True)
    return render(request, "rentals/home.html", {"featured": featured})


def all_villas(request):
    villas = Villa.objects.all()
    return render(request, "rentals/all_villas.html", {"villas": villas})


def featured_villas(request):
    villas = Villa.objects.filter(featured=True)
    return render(request, "rentals/featured_villas.html", {"featured_villas": villas})


# ---------------- SEARCH & FILTER ----------------

def search_villas(request):
    query = request.GET.get('q', '').strip()

    villas = Villa.objects.all()

    if query:
        villas = villas.filter(
            Q(name__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'rentals/search_results.html', {
        'villas': villas,
        'query': query
    })


def filter_villas(request):
    villas = Villa.objects.all()

    location = request.GET.get("location")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    if location:
        villas = villas.filter(location__icontains=location)

    if min_price and min_price.isdigit():
        villas = villas.filter(price_per_night__gte=min_price)

    if max_price and max_price.isdigit():
        villas = villas.filter(price_per_night__lte=max_price)

    return render(request, "rentals/filter.html", {"villas": villas})


# ---------------- STATIC PAGES ----------------

def about(request):
    return render(request, 'rentals/about.html')


def information(request):
    return render(request, "rentals/information.html")


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, "Message sent successfully!")
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'rentals/contact.html', {'form': form})


def faq(request):
    return render(request, "rentals/faq.html")


# ---------------- AUTH ----------------

from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password")
    else:
        form = AuthenticationForm()

    return render(request, 'rentals/login.html', {'form': form})

def logout_user(request):
    logout(request)
    return redirect('home')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )
            if user:
                login(request, user)
                return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'rentals/signup.html', {'form': form})


# ---------------- BOOKINGS ----------------

@login_required
def my_bookings_page(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, "rentals/my_bookings.html", {"bookings": bookings})


@login_required
def book_villa(request, villa_id):
    villa = get_object_or_404(Villa, id=villa_id)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.villa = villa
            booking.user = request.user
            booking.save()
            return redirect("my_bookings")
    else:
        form = BookingForm()

    return render(request, "rentals/booking_form.html", {"form": form, "villa": villa})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    booking.delete()
    return redirect("my_bookings")

#----------------- PAYMENT ----------------

@login_required
def payment_page(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    nights = (booking.end_date - booking.start_date).days
    total_price = nights * booking.villa.price_per_night

    if request.method == "POST":
        return redirect("payment_success")

    return render(request, "rentals/payment_page.html", {
        "booking": booking,
        "nights": nights,
        "total_price": total_price,
    })


@login_required
def payment_success(request):
    return render(request, "rentals/payment_success.html")

# ---------------- VILLA DETAILS & REVIEWS ----------------

def villa_detail(request, villa_id):
    villa = get_object_or_404(Villa, id=villa_id)
    reviews = Review.objects.filter(villa=villa)

    avg_rating = None
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()

    form = ReviewForm()

    if request.method == "POST" and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.villa = villa
            review.save()
            return redirect("villa_detail", villa_id=villa_id)

    return render(request, "rentals/villa_detail.html", {
        "villa": villa,
        "reviews": reviews,
        "avg_rating": avg_rating,
        "form": form,
    })


# ---------------- API ----------------

class VillaViewSet(viewsets.ModelViewSet):
    queryset = Villa.objects.all()
    serializer_class = VillaSerializer

    def get_serializer_context(self):
        return {'request': self.request}


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


# LOGIN API
@api_view(['POST'])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if user is not None:
        return Response({
            "success": True,
            "username": user.username,
            "email": user.email
        })
    else:
        return Response({"success": False})


# CREATE BOOKING API
@api_view(['POST'])
def create_booking(request):
    try:
        username = request.data.get("username")
        villa_id = request.data.get("villa_id")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        user = User.objects.get(username=username)
        villa = Villa.objects.get(id=villa_id)

        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        Booking.objects.create(
            villa=villa,
            user=user,
            guest_name=user.username,
            guest_email=user.email,
            start_date=start_date,
            end_date=end_date,
        )

        return Response({"success": True})

    except Exception as e:
        print("ERROR:", str(e))
        return Response({"success": False, "error": str(e)})


# MY BOOKINGS API
@api_view(['GET'])
def my_bookings(request):
    username = request.GET.get("username")

    try:
        user = User.objects.get(username=username)
        bookings = Booking.objects.filter(user=user)

        data = []
        for b in bookings:
            data.append({
                "id": b.id,
                "villa": b.villa.name,
                "start_date": str(b.start_date),
                "end_date": str(b.end_date),
                "price": str(b.villa.price_per_night),
            })

        return Response(data)

    except Exception as e:
        return Response({"error": str(e)})



#contact message api
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from .models import ContactMessage

@csrf_exempt
def contact_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            name = data.get("name")
            email = data.get("email")
            message = data.get("message")

            if not name or not email or not message:
                return JsonResponse({"success": False, "error": "Missing fields"})

            ContactMessage.objects.create(
                name=name,
                email=email,
                message=message
            )

            return JsonResponse({"success": True})

        except Exception as e:
            print("CONTACT ERROR:", str(e))
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False})

    # AJAX Search API
@api_view(['GET'])
def ajax_search(request):
    query = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    rooms = request.GET.get('rooms', '')
    guests = request.GET.get('guests', '')
    featured = request.GET.get('featured', '')

    villas = Villa.objects.all()

    if query:
        villas = villas.filter(
            Q(name__icontains=query) |
            Q(location__icontains=query) |
            Q(description__icontains=query)
        )
    if location:
        villas = villas.filter(location__icontains=location)
    if min_price:
        villas = villas.filter(price_per_night__gte=min_price)
    if max_price:
        villas = villas.filter(price_per_night__lte=max_price)
    if rooms:
        villas = villas.filter(number_of_rooms__gte=rooms)
    if guests:
        villas = villas.filter(max_guests__gte=guests)
    if featured == 'yes':
        villas = villas.filter(featured=True)

    data = []
    for v in villas:
        data.append({
            "id": v.id,
            "name": v.name,
            "location": v.location,
            "price_per_night": str(v.price_per_night),
            "image": request.build_absolute_uri(v.main_image.url) if v.main_image else None,
        })

    return Response(data)