import flet as ft
import requests

BASE_URL = "http://127.0.0.1:8000/api/"


def login_module(page: ft.Page, current_user: dict, on_success, on_register=None):
    username_input = ft.TextField(label="Username")
    password_input = ft.TextField(label="Password", password=True)

    def show_message(msg):
        snack = ft.SnackBar(content=ft.Text(msg))
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def login(e):
        res = requests.post(BASE_URL + "login/", json={
            "username": username_input.value,
            "password": password_input.value
        })
        data = res.json()
        if data.get("success"):
            current_user["username"] = data["username"]
            current_user["email"] = data["email"]
            on_success()
        else:
            show_message("Login failed ❌")

    return ft.Column([
        ft.Text("🏝️ Javan Rentals", size=30, weight="bold"),
        ft.Text("Login", size=20),
        username_input,
        password_input,
        ft.ElevatedButton("Login", on_click=login),
        ft.TextButton("Don't have an account? Register",
                      on_click=lambda e: on_register() if on_register else None)
    ], alignment="center", horizontal_alignment="center")


def logout_module(page: ft.Page, current_user: dict, on_logout):
    def logout(e):
        current_user["username"] = None
        current_user["email"] = None
        on_logout()

    return ft.OutlinedButton("Logout", on_click=logout)