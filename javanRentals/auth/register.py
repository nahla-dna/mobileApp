import flet as ft
import requests

BASE_URL = "http://127.0.0.1:8000/api/"


def register_module(page: ft.Page, on_success, on_back):
    username_input = ft.TextField(label="Username")
    email_input = ft.TextField(label="Email")
    password_input = ft.TextField(label="Password", password=True)
    confirm_input = ft.TextField(label="Confirm Password", password=True)

    def show_message(msg):
        snack = ft.SnackBar(content=ft.Text(msg))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def register(e):
        if password_input.value != confirm_input.value:
            show_message("Passwords do not match ❌")
            return

        res = requests.post(BASE_URL + "register/", json={
            "username": username_input.value,
            "email": email_input.value,
            "password": password_input.value
        })

        data = res.json()

        if data.get("success"):
            show_message("Account created! Please login ✅")
            on_success()  # go back to login
        else:
            show_message(data.get("error", "Registration failed ❌"))

    return ft.Column([
        ft.Text("🏝️ Javan Rentals", size=30, weight="bold"),
        ft.Text("Create Account", size=20),
        username_input,
        email_input,
        password_input,
        confirm_input,
        ft.ElevatedButton("Register", on_click=register),
        ft.TextButton("Already have an account? Login", on_click=lambda e: on_back())
    ], alignment="center", horizontal_alignment="center")