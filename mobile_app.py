import flet as ft
import requests
import asyncio
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/"

current_user = {"username": None, "email": None}


def main(page: ft.Page):
    page.title = "Javan Rentals Mobile"
    page.theme_mode = "dark"
    page.padding = 20

    villas_data = []

    # ---------------- UTIL ----------------
    def show_message(msg):
        snack = ft.SnackBar(content=ft.Text(msg))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # ---------------- LOGIN ----------------
    username_input = ft.TextField(label="Username")
    password_input = ft.TextField(label="Password", password=True)

    def login(e):
        res = requests.post(BASE_URL + "login/", json={
            "username": username_input.value,
            "password": password_input.value
        })

        data = res.json()

        if data.get("success"):
            current_user["username"] = data["username"]
            current_user["email"] = data["email"]
            load_villas()
        else:
            show_message("Login failed")

    def logout(e):
        current_user["username"] = None
        current_user["email"] = None
        page.controls.clear()
        page.add(login_ui())
        page.update()

    def login_ui():
        return ft.Column([
            ft.Text("Login", size=30, weight="bold"),
            username_input,
            password_input,
            ft.ElevatedButton("Login", on_click=login)
        ], alignment="center", horizontal_alignment="center")

    # ---------------- SEARCH + FILTER ----------------
    search_input = ft.TextField(label="Search villas...")

    location_filter = ft.TextField(label="Location")
    min_price = ft.TextField(label="Min Price")
    max_price = ft.TextField(label="Max Price")

    def apply_filters():
        filtered = villas_data

        if search_input.value:
            filtered = [v for v in filtered if search_input.value.lower() in v["name"].lower()]

        if location_filter.value:
            filtered = [v for v in filtered if location_filter.value.lower() in v["location"].lower()]

        if min_price.value:
            filtered = [v for v in filtered if float(v["price_per_night"]) >= float(min_price.value)]

        if max_price.value:
            filtered = [v for v in filtered if float(v["price_per_night"]) <= float(max_price.value)]

        display_villas(filtered)

    # ---------------- LOAD VILLAS ----------------
    def load_villas():
        page.controls.clear()

        res = requests.get(BASE_URL + "villas/")
        nonlocal villas_data
        villas_data = res.json()

        display_villas(villas_data)

    def display_villas(villas):
        cards = []

        for v in villas:
            def book(e, vid=v["id"], villa=v):
                open_booking(vid, villa)

            # Handle image safely
            image_url = v.get("image") or v.get("main_image")

            card = ft.Container(
                content=ft.Column([

                    # 🖼️ IMAGE SECTION
                    ft.Container(
                        content=ft.Image(
                            src=image_url,
                            fit="cover",
                            width=float("inf"),
                            height=180
                        ) if image_url else ft.Container(
                            content=ft.Text("No Image", color="white"),
                            alignment=ft.alignment.center,
                            height=180,
                            bgcolor="#333"
                        ),
                        border_radius=15,
                        clip_behavior=ft.ClipBehavior.HARD_EDGE
                    ),

                    # 🏠 TEXT INFO
                    ft.Column([
                        ft.Text(v["name"], size=18, weight="bold"),
                        ft.Text(f"📍 {v['location']}", size=13, color="grey"),
                        ft.Text(f"💰 Rs {v['price_per_night']}", size=14, weight="bold"),
                    ], spacing=3),

                    # 🔘 BUTTON
                    ft.ElevatedButton(
                        "Book Now",
                        on_click=book,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10)
                        )
                    )

                ], spacing=10),

                padding=12,
                border_radius=20,
                bgcolor="#1f1f1f",
                shadow=ft.BoxShadow(
                    blur_radius=10,
                    color="black",
                    offset=ft.Offset(2, 4)
                )
            )

            cards.append(card)

        page.controls.clear()
        page.add(
            ft.Text("🏝️ Javan Rentals", size=30, weight="bold"),

            ft.Row([
                ft.ElevatedButton("Bookings", on_click=lambda e: load_my_bookings()),
                ft.ElevatedButton("Contact", on_click=lambda e: contact_page()),
                ft.ElevatedButton("FAQ", on_click=lambda e: faq_page()),
                ft.OutlinedButton("Logout", on_click=logout),
            ]),

            search_input,
            ft.Row([location_filter, min_price, max_price]),
            ft.ElevatedButton("Apply Filters", on_click=lambda e: apply_filters()),

            ft.ListView(
                controls=cards,
                expand=True,
                spacing=15
            )
        )

        page.update()

    # ---------------- BOOKING (same as before) ----------------
    
    def close_dialog(dialog):
        dialog.open = False
        page.update()
    
    def open_booking(villa_id, villa):

        start = {"value": None}
        end = {"value": None}
        total = {"value": 0}

        total_text = ft.Text("Total: Rs 0", size=18, weight="bold")

        # ---------------- PRICE CALC ----------------
        def update():
            if start["value"] and end["value"]:
                d1 = datetime.strptime(start["value"], "%Y-%m-%d")
                d2 = datetime.strptime(end["value"], "%Y-%m-%d")
                nights = (d2 - d1).days

                if nights > 0:
                    price = float(villa["price_per_night"])
                    total["value"] = nights * price
                    total_text.value = f"Total: Rs {total['value']:.2f}"
                else:
                    total_text.value = "Invalid dates"

                page.update()

        # ---------------- DATE PICKERS ----------------
        def pick(field):
            def handler(e):
                val = e.control.value.strftime("%Y-%m-%d")
                field["value"] = val
                update()
            return handler

        dp_start = ft.DatePicker(on_change=pick(start))
        dp_end = ft.DatePicker(on_change=pick(end))

        page.overlay.extend([dp_start, dp_end])

        def open_dp(p):
            p.open = True
            page.update()

        start_btn = ft.ElevatedButton("Select Start Date", on_click=lambda e: open_dp(dp_start))
        end_btn = ft.ElevatedButton("Select End Date", on_click=lambda e: open_dp(dp_end))

        # ---------------- PAYMENT UI ----------------
        card_number = ft.TextField(label="Card Number", hint_text="1234 5678 9012 3456")
        card_name = ft.TextField(label="Card Holder Name")
        expiry = ft.TextField(label="Expiry (MM/YY)")
        cvv = ft.TextField(label="CVV", password=True)

        card_ui = ft.Container(
            content=ft.Column([
                ft.Text("💳 Payment Details", size=18, weight="bold"),
                card_number,
                card_name,
                ft.Row([expiry, cvv])
            ], spacing=10),
            padding=15,
            border_radius=15,
            bgcolor="#2a2a2a"
        )

        # ---------------- PAYMENT + BOOKING ----------------
        def pay(e):
            if not start["value"] or not end["value"]:
                show_message("Please select dates first 📅")
                return

            show_message("Processing payment... 💳")

            async def fake():
                await asyncio.sleep(2)

                # ✅ CREATE BOOKING AFTER PAYMENT
                response = requests.post(
                    BASE_URL + "create-booking/",
                    json={
                        "username": current_user["username"],
                        "villa_id": villa_id,
                        "start_date": start["value"],
                        "end_date": end["value"]
                    }
                )

                if response.status_code == 200 and response.json().get("success"):
                    show_message("Payment successful ✅ Booking confirmed 🎉")
                else:
                    show_message("Booking failed ❌")

                dialog.open = False
                page.update()

                load_villas()

            page.run_task(fake)

        # ---------------- DIALOG ----------------
        dialog = ft.AlertDialog(
            title=ft.Text("Book Villa"),
            content=ft.Column([
                start_btn,
                end_btn,
                total_text,
                card_ui
            ], tight=True),
            actions=[
                ft.ElevatedButton("Pay Now", on_click=pay),
                ft.TextButton("Cancel", on_click=lambda e: close_dialog(dialog))
            ]
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # ---------------- CONTACT ----------------
    def contact_page():
        name = ft.TextField(label="Name")
        email = ft.TextField(label="Email")
        msg = ft.TextField(label="Message", multiline=True)

        def send(e):
            show_message("Message sent ✅")

        page.controls.clear()
        page.add(
            ft.Text("Contact Us", size=25),
            name, email, msg,
            ft.ElevatedButton("Send", on_click=send),
            ft.TextButton("Back", on_click=lambda e: load_villas())
        )
        page.update()

    # ---------------- FAQ ----------------
    def faq_page():
        page.controls.clear()

        faqs = [
            ("How to book?", "Select villa and proceed."),
            ("Payment?", "Dummy payment."),
            ("Cancel?", "Contact support.")
        ]

        items = []
        for q, a in faqs:
            items.append(ft.ExpansionTile(title=ft.Text(q), controls=[ft.Text(a)]))

        page.add(
            ft.Text("FAQ", size=25),
            *items,
            ft.TextButton("Back", on_click=lambda e: load_villas())
        )
        page.update()

    # ---------------- BOOKINGS ----------------
    def load_my_bookings():
        page.controls.clear()
        res = requests.get(BASE_URL + f"mybookings/?username={current_user['username']}")
        data = res.json()

        items = [ft.Text(b["villa"]) for b in data]

        page.add(
            ft.Text("My Bookings"),
            *items,
            ft.TextButton("Back", on_click=lambda e: load_villas())
        )
        page.update()

    # START
    page.add(login_ui())


ft.app(target=main)