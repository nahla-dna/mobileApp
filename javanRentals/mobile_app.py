import flet as ft
import requests
import asyncio
from datetime import datetime

from auth.login import login_module, logout_module   # import login and logout
from auth.register import register_module #import registration

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

    # ---------------- SHOW LOGIN ----------------
    def show_login():
        page.controls.clear()
        page.add(login_module(page, current_user,
                          on_success=load_villas,
                          on_register=show_register))
        page.update()

    def show_register():
        page.controls.clear()
        page.add(register_module(page,
                             on_success=show_login,
                             on_back=show_login))
        page.update()

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

            image_url = v.get("image") or v.get("main_image")

            card = ft.Container(
                content=ft.Column([
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

                    ft.Column([
                        ft.Text(v["name"], size=18, weight="bold"),
                        ft.Text(f"📍 {v['location']}", size=13, color="grey"),
                        ft.Text(f"💰 Rs {v['price_per_night']}", size=14, weight="bold"),
                    ], spacing=3),

                    ft.ElevatedButton("Book Now", on_click=book)
                ], spacing=10),

                padding=12,
                border_radius=20,
                bgcolor="#1f1f1f"
            )

            cards.append(card)

        page.controls.clear()
        page.add(
            ft.Text("🏝️ Javan Rentals", size=30, weight="bold"),

            ft.Row([
                ft.ElevatedButton("Bookings", on_click=lambda e: load_my_bookings()),
                ft.ElevatedButton("Contact", on_click=lambda e: contact_page()),
                ft.ElevatedButton("FAQ", on_click=lambda e: faq_page()),
                logout_module(page, current_user, on_logout=show_login),  # 👈 logout button
            ]),

            search_input,
            ft.Row([location_filter, min_price, max_price]),
            ft.ElevatedButton("Apply Filters", on_click=lambda e: apply_filters()),

            ft.ListView(controls=cards, expand=True)
        )

        page.update()

    # ---------------- BOOKING ----------------
    def close_dialog(dialog):
        dialog.open = False
        page.update()

    def open_booking(villa_id, villa):
        start = {"value": None}
        end = {"value": None}
        total = {"value": 0}

        total_text = ft.Text("Total: Rs 0", size=18, weight="bold")

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

        def pay(e):
            if not start["value"] or not end["value"]:
                show_message("Please select dates first 📅")
                return

            async def fake():
                await asyncio.sleep(2)

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

        dialog = ft.AlertDialog(
            title=ft.Text("Book Villa"),
            content=ft.Column([start_btn, end_btn, total_text]),
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
        email = ft.TextField(label="Email", value=current_user["email"] or "")
        msg = ft.TextField(label="Message", multiline=True)

        def send(e):
            if not name.value or not email.value or not msg.value:
                show_message("Please fill all fields ❗")
                return

            try:
                response = requests.post(
                    BASE_URL + "contact/",
                    json={
                        "name": name.value,
                        "email": email.value,
                        "message": msg.value
                    }
                )

                if response.status_code == 200 and response.json().get("success"):
                    show_message("Message sent successfully ✅")
                    name.value = ""
                    email.value = ""
                    msg.value = ""
                    page.update()
                else:
                    show_message("Failed to send message ❌")

            except:
                show_message("Server error ❌")

        page.controls.clear()
        page.add(
            ft.Text("Contact Us", size=25, weight="bold"),
            name,
            email,
            msg,
            ft.ElevatedButton("Send", on_click=send),
            ft.TextButton("Back", on_click=lambda e: load_villas())
        )
        page.update()

    # ---------------- FAQ ----------------
    def faq_page():
        page.controls.clear()

        faqs = [
            ("How to book?", "Select villa and proceed."),
            ("Payment?", "Handled in app."),
            ("Cancel?", "Contact support.")
        ]

        items = [ft.ExpansionTile(title=ft.Text(q), controls=[ft.Text(a)]) for q, a in faqs]

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

    # ---------------- START ----------------
    show_login()


ft.app(target=main)