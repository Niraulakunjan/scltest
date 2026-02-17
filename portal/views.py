import json
import base64
from io import BytesIO
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth import login, logout
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .decorators import role_required
from .forms import (
    FeeRecordForm,
    HomeworkForm,
    NoticeForm,
    ParentCreateForm,
    StudentCreateForm,
    StyledAuthenticationForm,
)
from .models import (
    Attendance,
    AttendanceMethod,
    FeeRecord,
    Homework,
    Notice,
    NoticeAudience,
    ParentProfile,
    StudentProfile,
    UserRole,
)

try:
    import qrcode  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    qrcode = None


QR_SIGNER = signing.Signer(salt="schoolms-qr-attendance")


def build_student_qr_token(student_id):
    return QR_SIGNER.sign(str(student_id))


def resolve_student_id_from_qr(qr_data):
    raw_token = (qr_data or "").strip()
    if not raw_token:
        raise signing.BadSignature("Empty QR data")

    try:
        payload = json.loads(raw_token)
        if isinstance(payload, dict) and payload.get("token"):
            raw_token = payload["token"]
    except json.JSONDecodeError:
        pass

    unsigned = QR_SIGNER.unsign(raw_token)
    return int(unsigned)


def role_redirect(request):
    if not request.user.is_authenticated:
        return redirect("login")

    role = request.user.role
    if role == UserRole.ADMIN or request.user.is_superuser:
        return redirect("admin_dashboard")
    if role == UserRole.STUDENT:
        return redirect("student_dashboard")
    if role == UserRole.PARENT:
        return redirect("parent_dashboard")
    return redirect("login")


def login_view(request):
    if request.user.is_authenticated:
        return role_redirect(request)

    form = StyledAuthenticationForm(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return role_redirect(request)

    return render(request, "auth/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


@role_required(UserRole.ADMIN)
def admin_dashboard(request):
    today = timezone.localdate()
    total_students = StudentProfile.objects.count()
    present_today = Attendance.objects.filter(date=today).count()
    pending_fees = FeeRecord.objects.filter(total_amount__gt=0).aggregate(total=Sum("total_amount"), paid=Sum("paid_amount"))
    total_fee = pending_fees.get("total") or 0
    paid_fee = pending_fees.get("paid") or 0
    due_fee = total_fee - paid_fee

    context = {
        "today": today,
        "total_students": total_students,
        "present_today": present_today,
        "absent_today": max(total_students - present_today, 0),
        "recent_attendance": Attendance.objects.select_related("student", "student__user").all()[:12],
        "students_by_class": StudentProfile.objects.values("class_name").annotate(total=Count("id")).order_by("class_name"),
        "due_fee": due_fee,
        "notices": Notice.objects.all()[:5],
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@role_required(UserRole.ADMIN)
def manage_students(request):
    form = StudentCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        student = form.save()
        messages.success(
            request,
            f"Student created: {student.admission_no}. Login -> {student.user.username} / password set in form.",
        )
        return redirect("manage_students")

    students = StudentProfile.objects.select_related("user", "parent", "parent__user").all()
    return render(request, "dashboard/manage_students.html", {"form": form, "students": students})


@role_required(UserRole.ADMIN)
def manage_parents(request):
    form = ParentCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        parent = form.save()
        messages.success(
            request,
            f"Parent account created: {parent.user.username} / password set in form.",
        )
        return redirect("manage_parents")

    parents = ParentProfile.objects.select_related("user").annotate(children_count=Count("children")).order_by(
        "user__first_name"
    )
    return render(request, "dashboard/manage_parents.html", {"form": form, "parents": parents})


@role_required(UserRole.ADMIN)
def manage_academics(request):
    notice_form = NoticeForm(prefix="notice", data=request.POST or None)
    homework_form = HomeworkForm(prefix="homework", data=request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "notice" and notice_form.is_valid():
            notice = notice_form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            messages.success(request, "Notice published.")
            return redirect("manage_academics")
        if action == "homework" and homework_form.is_valid():
            homework = homework_form.save(commit=False)
            homework.created_by = request.user
            homework.save()
            messages.success(request, "Homework assigned.")
            return redirect("manage_academics")

    context = {
        "notice_form": notice_form,
        "homework_form": homework_form,
        "notices": Notice.objects.all()[:20],
        "homework_items": Homework.objects.all()[:20],
    }
    return render(request, "dashboard/manage_academics.html", context)


@role_required(UserRole.ADMIN)
def manage_fees(request):
    form = FeeRecordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Fee record saved.")
        return redirect("manage_fees")

    fee_records = FeeRecord.objects.select_related("student", "student__user").all()[:50]
    return render(request, "dashboard/manage_fees.html", {"form": form, "fee_records": fee_records})


@role_required(UserRole.ADMIN)
def attendance_scanner(request):
    today = timezone.localdate()
    attendance_today = Attendance.objects.select_related("student", "student__user").filter(date=today)
    students = StudentProfile.objects.select_related("user").order_by("admission_no")
    return render(
        request,
        "dashboard/attendance_scanner.html",
        {
            "attendance_today": attendance_today,
            "students": students,
            "today": today,
        },
    )


@role_required(UserRole.ADMIN)
@require_POST
def manual_attendance_mark(request):
    student_id = request.POST.get("student_id")
    student = get_object_or_404(StudentProfile, pk=student_id)
    attendance, created = Attendance.objects.get_or_create(
        student=student,
        date=timezone.localdate(),
        defaults={"method": AttendanceMethod.MANUAL, "marked_by": request.user},
    )
    if created:
        messages.success(request, f"Attendance marked for {student.admission_no}.")
    else:
        messages.info(request, f"Attendance already marked for {student.admission_no} today.")
    return redirect("attendance_scanner")


@role_required(UserRole.ADMIN)
@require_POST
def scan_qr_attendance(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "Invalid JSON payload"}, status=400)

    qr_data = payload.get("qr_data", "")
    try:
        student_id = resolve_student_id_from_qr(qr_data)
    except signing.BadSignature:
        return JsonResponse({"ok": False, "message": "QR is invalid or tampered."}, status=400)
    except ValueError:
        return JsonResponse({"ok": False, "message": "QR payload is malformed."}, status=400)

    student = get_object_or_404(StudentProfile.objects.select_related("user"), pk=student_id)
    attendance, created = Attendance.objects.get_or_create(
        student=student,
        date=timezone.localdate(),
        defaults={"method": AttendanceMethod.QR, "marked_by": request.user},
    )

    if created:
        return JsonResponse(
            {
                "ok": True,
                "status": "marked",
                "message": f"Attendance marked for {student.user.get_full_name() or student.user.username}",
                "student": student.admission_no,
            }
        )

    marked_time = timezone.localtime(attendance.marked_at).strftime("%I:%M %p")
    return JsonResponse(
        {
            "ok": True,
            "status": "already_marked",
            "message": f"Already marked today at {marked_time}",
            "student": student.admission_no,
        }
    )


@role_required(UserRole.STUDENT)
def student_dashboard(request):
    try:
        student = request.user.student_profile
    except ObjectDoesNotExist:
        messages.error(request, "Student profile missing. Contact admin.")
        return redirect("logout")

    today = timezone.localdate()
    qr_payload = {
        "token": build_student_qr_token(student.id),
        "admission_no": student.admission_no,
        "name": student.user.get_full_name() or student.user.username,
    }

    notices = Notice.objects.filter(audience__in=[NoticeAudience.ALL, NoticeAudience.STUDENT])[:10]
    homework_items = Homework.objects.filter(class_name=student.class_name)[:10]
    fees = student.fee_records.all()[:10]
    attendance_records = student.attendance_records.all()[:20]

    qr_payload_text = json.dumps(qr_payload, separators=(",", ":"))
    qr_image_src = f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&data={quote(qr_payload_text, safe='')}"

    # Prefer local QR generation when optional dependency is available.
    if qrcode is not None:
        qr_img = qrcode.make(qr_payload_text)
        qr_buf = BytesIO()
        qr_img.save(qr_buf, format="PNG")
        qr_image_src = f"data:image/png;base64,{base64.b64encode(qr_buf.getvalue()).decode('ascii')}"

    context = {
        "student": student,
        "today": today,
        "today_attendance": student.attendance_records.filter(date=today).first(),
        "attendance_records": attendance_records,
        "notices": notices,
        "homework_items": homework_items,
        "fees": fees,
        "qr_payload": qr_payload_text,
        "qr_image_src": qr_image_src,
    }
    return render(request, "dashboard/student_dashboard.html", context)


@role_required(UserRole.PARENT)
def parent_dashboard(request):
    try:
        parent = request.user.parent_profile
    except ObjectDoesNotExist:
        messages.error(request, "Parent profile missing. Contact admin.")
        return redirect("logout")

    children = parent.children.select_related("user").all()
    selected_child_id = request.GET.get("child")
    selected_child = None

    if selected_child_id:
        selected_child = children.filter(id=selected_child_id).first()
    if not selected_child and children:
        selected_child = children[0]

    attendance_records = selected_child.attendance_records.all()[:15] if selected_child else []
    fee_records = selected_child.fee_records.all()[:10] if selected_child else []
    notices = Notice.objects.filter(audience__in=[NoticeAudience.ALL, NoticeAudience.PARENT])[:10]

    context = {
        "children": children,
        "selected_child": selected_child,
        "attendance_records": attendance_records,
        "fee_records": fee_records,
        "notices": notices,
    }
    return render(request, "dashboard/parent_dashboard.html", context)
