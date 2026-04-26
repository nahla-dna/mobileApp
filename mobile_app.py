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

    page.title = "Javan Rentals Mobile"
    page.theme_mode = "dark"
    page.padding = 20
    page.window_resizable = True  
    page.window_min_width = 360   # ← minimum width
    page.window_min_height = 600  # ← minimum height

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
    search_input = ft.TextField(label="Search villas...", on_change=lambda e: apply_filters())
    location_filter = ft.TextField(label="Location", autofocus=False, on_change=lambda e: apply_filters())
    min_price = ft.TextField(label="Min Price", autofocus=False, on_change=lambda e: apply_filters())
    max_price = ft.TextField(label="Max Price", autofocus=False, on_change=lambda e: apply_filters())
    villa_list_view = ft.ListView(expand=True)  

    def apply_filters():
        params = {}

        if search_input.value:
            params["q"] = search_input.value
        if location_filter.value:
            params["location"] = location_filter.value
        if min_price.value:
            params["min_price"] = min_price.value
        if max_price.value:
            params["max_price"] = max_price.value

        try:
            res = requests.get(BASE_URL + "search/", params=params)
            filtered = res.json()
        except:
            filtered = []

        villa_list_view.controls = build_cards(filtered)
        page.update()

    # ---------------- LOAD VILLAS ----------------
    def load_villas():
        page.controls.clear()

        res = requests.get(BASE_URL + "villas/")
        nonlocal villas_data
        villas_data = res.json()

        display_villas(villas_data)

    def build_cards(villas):
        cards = []
        for v in villas:
            def book(e, vid=v["id"], villa=v):
                open_booking(vid, villa)
            image_url = v.get("image") or v.get("main_image")
            card = ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Image(src=image_url, fit="cover", width=float("inf"), height=180)
                        if image_url else ft.Container(
                            content=ft.Text("No Image", color="white"),
                            alignment=ft.alignment.Alignment(0, 0), height=180, bgcolor="#333"
                        ),
                        border_radius=15, clip_behavior=ft.ClipBehavior.HARD_EDGE
                    ),
                    ft.Column([
                        ft.Text(v["name"], size=18, weight="bold"),
                        ft.Text(f"📍 {v['location']}", size=13, color="grey"),
                        ft.Text(f"💰 Rs {v['price_per_night']}", size=14, weight="bold"),
                    ], spacing=3),
                    ft.ElevatedButton("Book Now", on_click=book)
                ], spacing=10),
                padding=12, border_radius=20, bgcolor="#1f1f1f"
            )
            cards.append(card)
        return cards

    def display_villas(villas):
        villa_list_view.controls = build_cards(villas)
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
            villa_list_view  # ← reuse the same ListView, no rebuild
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

    # ---------------- CONTACT (UPDATED 🔥) ----------------
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

                    # clear fields
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

    # START
    page.add(login_ui())


ft.app(target=main)