from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("staff-dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    
    # ADMIN
    path("admin-login/", views.admin_login, name="admin_login"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-students/", views.admin_students, name="admin_students"),
    path("admin-attendance/", views.admin_attendance, name="admin_attendance"),
    path("admin-teachers/", views.admin_teachers, name="admin_teachers"),
    path("admin-reports/", views.admin_reports, name="admin_reports"),
    path("admin-logout/", views.admin_logout, name="admin_logout"),
]
