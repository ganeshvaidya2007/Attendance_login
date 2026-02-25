from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product

User = get_user_model()


def _resolve_auth_user(identifier):
    return (
        User.objects.filter(username=identifier).first()
        or User.objects.filter(username__iexact=identifier).first()
        or User.objects.filter(gmail__iexact=identifier).first()
        or User.objects.filter(email__iexact=identifier).first()
    )


def _role_redirect_name(user):
    if user.is_superuser:
        return "admin_dashboard"
    if user.is_staff:
        return "staff_dashboard"
    return "student_dashboard"


# LOGIN VIEW
def login_user(request):
    if request.user.is_authenticated:
        return redirect(_role_redirect_name(request.user))

    if request.method == "POST":
        identifier = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        role = request.POST.get("role", "student").lower()

        matched_user = _resolve_auth_user(identifier)
        auth_username = matched_user.username if matched_user else identifier

        user = authenticate(request, username=auth_username, password=password)

        if user is not None:
            role_ok = (
                (role == "admin" and user.is_superuser)
                or (role == "staff" and user.is_staff and not user.is_superuser)
                or (role == "student" and not user.is_staff)
            )
            if not role_ok:
                messages.error(request, f"This account does not have {role.title()} access.")
                return render(request, "login.html", {"selected_role": role, "typed_username": identifier})

            login(request, user)
            return redirect(_role_redirect_name(user))
        else:
            messages.error(request, "Invalid username or password")
            return render(request, "login.html", {"selected_role": role, "typed_username": identifier})

    return render(request, "login.html", {"selected_role": "student"})


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


@login_required(login_url="login")
@user_passes_test(lambda u: u.is_staff and not u.is_superuser, login_url="login")
def staff_dashboard(request):
    context = {
        "teacher_count": 3,
        "student_count": User.objects.filter(is_staff=False, is_superuser=False).count(),
        "attendance_sessions": 24,
    }
    return render(request, "staff_dashboard.html", context)


@login_required(login_url="login")
@user_passes_test(lambda u: not u.is_staff, login_url="login")
def student_dashboard(request):
    context = {
        "student_total": User.objects.filter(is_staff=False, is_superuser=False).count(),
        "overall_pct": 86.2,
        "recent_notices": [
            "Mid-term exams start next Monday.",
            "Attendance review meeting on Friday.",
            "Lab submissions close this week.",
        ],
    }
    return render(request, "student_dashboard.html", context)


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard")

    if request.method == "POST":
        identifier = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        matched_user = _resolve_auth_user(identifier)
        auth_username = matched_user.username if matched_user else identifier

        user = authenticate(request, username=auth_username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect("admin_dashboard")

        if user is not None and not user.is_staff:
            messages.error(request, "This account does not have admin access.")
            return render(request, "admin_login.html")

        messages.error(request, "Invalid admin credentials")

    return render(request, "admin_login.html")


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_dashboard(request):
    total_students = User.objects.filter(is_staff=False, is_superuser=False).count()
    classes_conducted = Product.objects.count()

    monthly_attendance = [
        {"month": "Jan", "value": 84},
        {"month": "Feb", "value": 88},
        {"month": "Mar", "value": 82},
        {"month": "Apr", "value": 91},
        {"month": "May", "value": 87},
        {"month": "Jun", "value": 85},
    ]

    recent_activity = [
        {"title": "Attendance marked for CS-6A", "time": "10 mins ago"},
        {"title": "New student added", "time": "1 hour ago"},
        {"title": "Monthly report generated", "time": "3 hours ago"},
    ]

    context = {
        "total_students": total_students,
        "classes_conducted": classes_conducted,
        "avg_attendance": round(sum(item["value"] for item in monthly_attendance) / len(monthly_attendance), 1),
        "classes_today": 3,
        "monthly_attendance": monthly_attendance,
        "recent_activity": recent_activity,
        "department_distribution": {"CS": 32, "IS": 24, "EC": 21, "ME": 23},
    }

    return render(request, "admin_dashboard.html", context)


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_students(request):
    students = [
        {"name": "Alice Carter", "usn": "1CS21001", "branch": "CS", "sem": 6, "sec": "A"},
        {"name": "Bob Dawson", "usn": "1CS21002", "branch": "CS", "sem": 6, "sec": "A"},
        {"name": "Charlie Evans", "usn": "1CS21003", "branch": "CS", "sem": 6, "sec": "B"},
        {"name": "Diana Foster", "usn": "1CS21004", "branch": "IS", "sem": 4, "sec": "A"},
        {"name": "Ethan Grant", "usn": "1CS21005", "branch": "EC", "sem": 8, "sec": "C"},
        {"name": "Fiona Hill", "usn": "1CS21006", "branch": "CS", "sem": 6, "sec": "A"},
        {"name": "George Ives", "usn": "1CS21007", "branch": "ME", "sem": 2, "sec": "A"},
        {"name": "Hannah Jones", "usn": "1CS21008", "branch": "CS", "sem": 6, "sec": "B"},
    ]
    return render(request, "admin_students.html", {"students": students})


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_attendance(request):
    students = [
        {"name": "Alice Carter", "usn": "1CS21001"},
        {"name": "Bob Dawson", "usn": "1CS21002"},
        {"name": "Charlie Evans", "usn": "1CS21003"},
        {"name": "Diana Foster", "usn": "1CS21004"},
        {"name": "Ethan Grant", "usn": "1CS21005"},
        {"name": "Fiona Hill", "usn": "1CS21006"},
        {"name": "George Ives", "usn": "1CS21007"},
        {"name": "Hannah Jones", "usn": "1CS21008"},
    ]
    context = {
        "students": students,
        "class_options": ["CS - 6A", "CS - 6B", "IS - 4A", "EC - 8C", "ME - 2A"],
        "subject_options": ["Web Technologies", "Data Structures", "Algorithms", "Operating Systems"],
    }
    return render(request, "admin_attendance.html", context)


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_teachers(request):
    teachers = [
        {"name": "Dr. Sarah Smith", "email": "sarah@college.edu", "subject": "Data Structures"},
        {"name": "Prof. Alan Turing", "email": "alan@college.edu", "subject": "Algorithms"},
        {"name": "Prof. Grace Hopper", "email": "grace@college.edu", "subject": "Operating Systems"},
    ]
    return render(request, "admin_teachers.html", {"teachers": teachers})


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_reports(request):
    context = {
        "monthly_average": 88.2,
        "critical_attendance": 12,
        "best_class": "CS-6A",
        "best_class_avg": 94,
        "subject_breakdown": [
            {"subject": "Web Tech", "value": 82, "critical": False},
            {"subject": "ML", "value": 79, "critical": False},
            {"subject": "Cloud", "value": 81, "critical": False},
            {"subject": "OS", "value": 75, "critical": True},
            {"subject": "DSA", "value": 80, "critical": False},
        ],
        "shortage": [
            {"name": "George Ives", "usn": "1CS21007", "attendance": 62, "status": "Critical"},
            {"name": "Diana Foster", "usn": "1CS21004", "attendance": 71, "status": "Warning"},
        ],
    }
    return render(request, "admin_reports.html", context)


@login_required(login_url="admin_login")
def admin_logout(request):
    logout(request)
    return redirect("admin_login")


def user_logout(request):
    logout(request)
    return redirect("login")
