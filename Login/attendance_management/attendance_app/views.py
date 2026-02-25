from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import AttendanceRecord, Product, Student, Teacher

User = get_user_model()

CLASS_OPTIONS = ["CS - 6A", "CS - 6B", "IS - 4A", "EC - 8C", "ME - 2A"]
SUBJECT_OPTIONS = ["Web Technologies", "Data Structures", "Algorithms", "Operating Systems", "ML"]


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


def home(request):
    return render(request, "home.html")


def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("register")

        User.objects.create_user(
            username=username,
            password=password,
            gmail=f"{username}@example.com",
            phonenumber="0000000000",
        )
        messages.success(request, "Registration successful")
        return redirect("login")

    return render(request, "register.html")


def user_login(request):
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

        messages.error(request, "Invalid username or password")
        return render(request, "login.html", {"selected_role": role, "typed_username": identifier})

    return render(request, "login.html", {"selected_role": "student"})


def user_logout(request):
    logout(request)
    return redirect("login")


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


def _ensure_demo_data():
    if not Student.objects.exists():
        Student.objects.bulk_create(
            [
                Student(name="Alice Carter", usn="1CS21001", branch="CS", sem=6, sec="A"),
                Student(name="Bob Dawson", usn="1CS21002", branch="CS", sem=6, sec="A"),
                Student(name="Charlie Evans", usn="1CS21003", branch="CS", sem=6, sec="B"),
                Student(name="Diana Foster", usn="1CS21004", branch="IS", sem=4, sec="A"),
                Student(name="Ethan Grant", usn="1CS21005", branch="EC", sem=8, sec="C"),
                Student(name="Fiona Hill", usn="1CS21006", branch="CS", sem=6, sec="A"),
                Student(name="George Ives", usn="1CS21007", branch="ME", sem=2, sec="A"),
                Student(name="Hannah Jones", usn="1CS21008", branch="CS", sem=6, sec="B"),
            ]
        )

    if not Teacher.objects.exists():
        Teacher.objects.bulk_create(
            [
                Teacher(name="Dr. Sarah Smith", email="sarah@college.edu", subject="Data Structures"),
                Teacher(name="Prof. Alan Turing", email="alan@college.edu", subject="Algorithms"),
                Teacher(name="Prof. Grace Hopper", email="grace@college.edu", subject="Operating Systems"),
            ]
        )

    if not AttendanceRecord.objects.exists():
        students = list(Student.objects.all())
        today = timezone.localdate()
        subjects = ["Web Technologies", "ML", "Cloud", "OS", "DSA"]
        for day_offset in range(0, 30):
            attendance_date = today - timedelta(days=day_offset)
            for student in students:
                score = (student.id + attendance_date.day + attendance_date.month) % 10
                is_present = score > 1
                if student.usn in {"1CS21007", "1CS21004"}:
                    is_present = score > 3
                AttendanceRecord.objects.create(
                    student=student,
                    date=attendance_date,
                    class_section=f"{student.branch} - {student.sem}{student.sec}",
                    subject=subjects[day_offset % len(subjects)],
                    is_present=is_present,
                )


def _students_for_class(class_section):
    branch = "CS"
    sem = 6
    sec = "A"
    if " - " in class_section:
        branch, group = class_section.split(" - ", 1)
        sem = int(group[0]) if group and group[0].isdigit() else 6
        sec = group[1] if len(group) > 1 else "A"
    return Student.objects.filter(branch=branch, sem=sem, sec=sec)


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_dashboard(request):
    _ensure_demo_data()
    total_students = Student.objects.count()
    classes_conducted = (
        AttendanceRecord.objects.values("date", "class_section", "subject").distinct().count()
    )
    monthly_attendance = [
        {"month": "Jan", "value": 84},
        {"month": "Feb", "value": 88},
        {"month": "Mar", "value": 82},
        {"month": "Apr", "value": 91},
        {"month": "May", "value": 87},
        {"month": "Jun", "value": 85},
    ]
    recent_records = AttendanceRecord.objects.select_related("student")[:3]
    recent_activity = [
        {"title": f"Attendance marked for {item.class_section}", "time": "recently"}
        for item in recent_records
    ]
    if not recent_activity:
        recent_activity = [
            {"title": "Attendance marked for CS-6A", "time": "10 mins ago"},
            {"title": "New student added", "time": "1 hour ago"},
            {"title": "Monthly report generated", "time": "3 hours ago"},
        ]

    context = {
        "active_page": "dashboard",
        "total_students": total_students,
        "classes_conducted": classes_conducted,
        "avg_attendance": round(sum(item["value"] for item in monthly_attendance) / len(monthly_attendance), 1),
        "classes_today": 3,
        "monthly_attendance": monthly_attendance,
        "recent_activity": recent_activity,
        "department_distribution": {"CS": 32, "IS": 24, "EC": 21, "ME": 23},
    }
    return render(request, "admin_dashboard.html", context)


@login_required(login_url="login")
@user_passes_test(lambda u: u.is_staff and not u.is_superuser, login_url="login")
def staff_dashboard(request):
    _ensure_demo_data()
    context = {
        "teacher_count": Teacher.objects.count(),
        "student_count": Student.objects.count(),
        "attendance_sessions": AttendanceRecord.objects.values("date", "class_section", "subject").distinct().count(),
    }
    return render(request, "staff_dashboard.html", context)


@login_required(login_url="login")
@user_passes_test(lambda u: not u.is_staff, login_url="login")
def student_dashboard(request):
    _ensure_demo_data()
    student_total = Student.objects.count()
    overall_total = AttendanceRecord.objects.count()
    overall_present = AttendanceRecord.objects.filter(is_present=True).count()
    overall_pct = round((overall_present / overall_total) * 100, 1) if overall_total else 0
    context = {
        "student_total": student_total,
        "overall_pct": overall_pct,
        "recent_notices": [
            "Mid-term exams start next Monday.",
            "Attendance review meeting on Friday.",
            "Lab submissions close this week.",
        ],
    }
    return render(request, "student_dashboard.html", context)


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_students(request):
    _ensure_demo_data()

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        usn = request.POST.get("usn", "").strip().upper()
        branch = request.POST.get("branch", "CS").strip().upper()
        sem = int(request.POST.get("sem", "1"))
        sec = request.POST.get("sec", "A").strip().upper()
        if name and usn:
            Student.objects.update_or_create(
                usn=usn,
                defaults={"name": name, "branch": branch, "sem": sem, "sec": sec},
            )
            messages.success(request, "Student saved.")
            return redirect("admin_students")

    search = request.GET.get("q", "").strip()
    branch = request.GET.get("branch", "ALL").strip().upper()
    sem = request.GET.get("sem", "ALL").strip().upper()

    students = Student.objects.all()
    if search:
        students = students.filter(Q(name__icontains=search) | Q(usn__icontains=search))
    if branch != "ALL":
        students = students.filter(branch=branch)
    if sem != "ALL" and sem.isdigit():
        students = students.filter(sem=int(sem))

    context = {
        "active_page": "students",
        "students": students.order_by("name"),
        "search": search,
        "selected_branch": branch,
        "selected_sem": sem,
        "branch_options": ["ALL", "CS", "IS", "EC", "ME"],
        "sem_options": ["ALL", "1", "2", "3", "4", "5", "6", "7", "8"],
    }
    return render(request, "admin_students.html", context)


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_attendance(request):
    _ensure_demo_data()

    selected_date = request.POST.get("attendance_date") or request.GET.get("date") or str(timezone.localdate())
    selected_class = request.POST.get("class_section") or request.GET.get("class") or "CS - 6A"
    selected_subject = request.POST.get("subject") or request.GET.get("subject") or "Web Technologies"

    students = _students_for_class(selected_class)

    if request.method == "POST" and request.POST.get("action") == "save":
        present_ids = {int(student_id) for student_id in request.POST.getlist("present_students")}
        for student in students:
            AttendanceRecord.objects.update_or_create(
                student=student,
                date=selected_date,
                subject=selected_subject,
                class_section=selected_class,
                defaults={"is_present": student.id in present_ids},
            )
        messages.success(request, "Attendance saved successfully.")
        return redirect("admin_attendance")

    status_map = {
        record.student_id: record.is_present
        for record in AttendanceRecord.objects.filter(
            date=selected_date, class_section=selected_class, subject=selected_subject
        )
    }
    student_rows = [{"obj": student, "present": status_map.get(student.id, True)} for student in students]

    context = {
        "active_page": "attendance",
        "class_options": CLASS_OPTIONS,
        "subject_options": SUBJECT_OPTIONS,
        "selected_class": selected_class,
        "selected_subject": selected_subject,
        "selected_date": selected_date,
        "student_rows": student_rows,
    }
    return render(request, "admin_attendance.html", context)


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_teachers(request):
    _ensure_demo_data()
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        subject = request.POST.get("subject", "").strip()
        if name and email and subject:
            Teacher.objects.update_or_create(email=email, defaults={"name": name, "subject": subject})
            messages.success(request, "Teacher saved.")
            return redirect("admin_teachers")

    context = {"active_page": "teachers", "teachers": Teacher.objects.all()}
    return render(request, "admin_teachers.html", context)


@login_required(login_url="admin_login")
@user_passes_test(lambda u: u.is_staff, login_url="admin_login")
def admin_reports(request):
    _ensure_demo_data()
    records = AttendanceRecord.objects.select_related("student")
    total = records.count()
    present = records.filter(is_present=True).count()
    monthly_average = round((present / total) * 100, 1) if total else 0

    student_stats = []
    for student in Student.objects.all():
        student_records = records.filter(student=student)
        total_classes = student_records.count()
        present_classes = student_records.filter(is_present=True).count()
        attendance_pct = round((present_classes / total_classes) * 100, 1) if total_classes else 0
        student_stats.append({"student": student, "attendance_pct": attendance_pct})

    shortage = sorted([s for s in student_stats if s["attendance_pct"] < 75], key=lambda x: x["attendance_pct"])
    critical_attendance = len(shortage)

    class_map = {}
    for record in records:
        class_map.setdefault(record.class_section, {"total": 0, "present": 0})
        class_map[record.class_section]["total"] += 1
        if record.is_present:
            class_map[record.class_section]["present"] += 1

    best_class = "CS-6A"
    best_class_avg = 0
    for class_name, stats in class_map.items():
        avg = round((stats["present"] / stats["total"]) * 100, 1) if stats["total"] else 0
        if avg > best_class_avg:
            best_class_avg = avg
            best_class = class_name

    subject_breakdown = []
    for subject in SUBJECT_OPTIONS:
        subject_total = records.filter(subject=subject).count()
        subject_present = records.filter(subject=subject, is_present=True).count()
        pct = round((subject_present / subject_total) * 100, 1) if subject_total else 0
        subject_breakdown.append({"subject": subject, "value": pct})

    context = {
        "active_page": "reports",
        "monthly_average": monthly_average,
        "critical_attendance": critical_attendance,
        "best_class": best_class,
        "best_class_avg": best_class_avg,
        "subject_breakdown": subject_breakdown,
        "shortage": shortage[:5],
    }
    return render(request, "admin_reports.html", context)


@login_required(login_url="admin_login")
def admin_logout(request):
    logout(request)
    return redirect("admin_login")
