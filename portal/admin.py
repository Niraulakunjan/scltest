from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Attendance, FeeRecord, Homework, Notice, ParentProfile, StudentProfile, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("Role", {"fields": ("role", "phone")}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("admission_no", "user", "class_name", "section", "parent")
    search_fields = ("admission_no", "user__first_name", "user__last_name", "user__username")


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "occupation", "emergency_contact")
    search_fields = ("user__first_name", "user__last_name", "user__username")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "method", "marked_by", "marked_at")
    list_filter = ("date", "method")
    search_fields = ("student__admission_no", "student__user__first_name", "student__user__last_name")


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "created_by", "created_at")
    list_filter = ("audience",)


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ("title", "class_name", "subject", "due_date", "created_by")
    list_filter = ("class_name", "due_date")


@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "term", "total_amount", "paid_amount", "due_date")
    list_filter = ("due_date",)
