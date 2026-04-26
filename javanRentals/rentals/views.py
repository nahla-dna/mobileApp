from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse
from django.db.models import Q
from datetime import datetime
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Villa, Booking, Review, ContactMessage
from .forms import ContactForm, SignUpForm, BookingForm, ReviewForm
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.contrib.auth.forms import AuthenticationForm

from .serializers import VillaSerializer, ReviewSerializer, BookingSerializer
from math import radians, cos, sin, asin, sqrt


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


# ---------------- AUTH (WEB) ----------------

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


# ---------------- PAYMENT ----------------

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
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_context(self):
        return {'request': self.request}


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]


# LOGIN API
@api_view(['POST'])
@permission_classes([AllowAny])
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


# REGISTER API
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if User.objects.filter(username=username).exists():
        return Response({"success": False, "error": "Username already taken"})

    User.objects.create_user(username=username, email=email, password=password)
    return Response({"success": True})


# CREATE BOOKING API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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


# CONTACT MESSAGE API
@api_view(['POST'])
@permission_classes([AllowAny])
def contact_api(request):
    try:
        name = request.data.get("name")
        email = request.data.get("email")
        message = request.data.get("message")

        if not name or not email or not message:
            return Response({"success": False, "error": "Missing fields"})

        ContactMessage.objects.create(name=name, email=email, message=message)
        return Response({"success": True})

    except Exception as e:
        print("CONTACT ERROR:", str(e))
        return Response({"success": False, "error": str(e)})


# ---------------- NEARBY VILLAS API ----------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return R * 2 * asin(sqrt(a))


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def villas_nearby(request):
    try:
        user_lat = float(request.GET.get('lat'))
        user_lon = float(request.GET.get('lon'))
        radius_km = float(request.GET.get('radius', 50))
    except (TypeError, ValueError):
        return Response({'error': 'Please provide valid lat and lon values.'}, status=400)

    villas = Villa.objects.exclude(latitude=None).exclude(longitude=None)

    nearby = []
    for villa in villas:
        dist = haversine(user_lat, user_lon, float(villa.latitude), float(villa.longitude))
        if dist <= radius_km:
            nearby.append({
                'id': villa.id,
                'name': villa.name,
                'location': villa.location,
                'price_per_night': str(villa.price_per_night),
                'latitude': str(villa.latitude),
                'longitude': str(villa.longitude),
                'distance_km': round(dist, 2),
            })

    nearby.sort(key=lambda x: x['distance_km'])
    return Response(nearby)