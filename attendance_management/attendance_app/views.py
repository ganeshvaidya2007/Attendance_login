from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()


# LOGIN VIEW
def login_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


# REGISTER VIEW  ✅ THIS IS THE IMPORTANT ONE
def register_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        gmail = request.POST.get("gmail")
        password = request.POST.get("password")

        # basic validation
        if not username or not gmail or not password:
            messages.error(request, "All fields are required")
            return render(request, "register.html")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, "register.html")

        if User.objects.filter(gmail=gmail).exists():
            messages.error(request, "Gmail already registered")
            return render(request, "register.html")

        # CREATE USER (IMPORTANT)
        User.objects.create_user(
            username=username,
            password=password,
            gmail=gmail
        )

        messages.success(request, "Registration successful. Please login.")
        return redirect("login")

    return render(request, "register.html")


# HOME VIEW
def home(request):
    return render(request, "home.html")