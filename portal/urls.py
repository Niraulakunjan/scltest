from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("redirect/", views.role_redirect, name="role_redirect"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/admin/students/", views.manage_students, name="manage_students"),
    path("dashboard/admin/parents/", views.manage_parents, name="manage_parents"),
    path("dashboard/admin/academics/", views.manage_academics, name="manage_academics"),
    path("dashboard/admin/fees/", views.manage_fees, name="manage_fees"),
    path("dashboard/admin/attendance/", views.attendance_scanner, name="attendance_scanner"),
    path("dashboard/admin/attendance/manual/", views.manual_attendance_mark, name="manual_attendance_mark"),
    path("dashboard/admin/attendance/scan/", views.scan_qr_attendance, name="scan_qr_attendance"),
    path("dashboard/student/", views.student_dashboard, name="student_dashboard"),
    path("dashboard/parent/", views.parent_dashboard, name="parent_dashboard"),
]
