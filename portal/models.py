from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    STUDENT = "STUDENT", "Student"
    PARENT = "PARENT", "Parent"


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError("The username must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.STUDENT)
    phone = models.CharField(max_length=20, blank=True)

    objects = UserManager()


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="parent_profile")
    occupation = models.CharField(max_length=120, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)

    def save(self, *args, **kwargs):
        if self.user.role != UserRole.PARENT:
            self.user.role = UserRole.PARENT
            self.user.save(update_fields=["role"])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Parent: {self.user.get_full_name() or self.user.username}"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    admission_no = models.CharField(max_length=25, unique=True)
    class_name = models.CharField(max_length=25)
    section = models.CharField(max_length=10, blank=True)
    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["class_name", "admission_no"]

    def save(self, *args, **kwargs):
        if self.user.role != UserRole.STUDENT:
            self.user.role = UserRole.STUDENT
            self.user.save(update_fields=["role"])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.admission_no} - {self.user.get_full_name() or self.user.username}"


class AttendanceMethod(models.TextChoices):
    QR = "QR", "QR Scan"
    MANUAL = "MANUAL", "Manual"


class Attendance(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(default=timezone.localdate)
    marked_at = models.DateTimeField(default=timezone.now)
    method = models.CharField(max_length=12, choices=AttendanceMethod.choices, default=AttendanceMethod.QR)
    marked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_attendance",
    )

    class Meta:
        unique_together = ("student", "date")
        ordering = ["-date", "-marked_at"]

    def __str__(self):
        return f"{self.student.admission_no} - {self.date}"


class NoticeAudience(models.TextChoices):
    ALL = "ALL", "All"
    STUDENT = "STUDENT", "Students"
    PARENT = "PARENT", "Parents"


class Notice(models.Model):
    title = models.CharField(max_length=120)
    message = models.TextField()
    audience = models.CharField(max_length=12, choices=NoticeAudience.choices, default=NoticeAudience.ALL)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Homework(models.Model):
    class_name = models.CharField(max_length=25)
    subject = models.CharField(max_length=80)
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    due_date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "-created_at"]

    def __str__(self):
        return f"{self.class_name} - {self.subject}"


class FeeRecord(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="fee_records")
    term = models.CharField(max_length=40)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_date", "-created_at"]

    @property
    def due_amount(self):
        return max(self.total_amount - self.paid_amount, 0)

    @property
    def is_paid(self):
        return self.due_amount == 0

    def __str__(self):
        return f"{self.student.admission_no} - {self.term}"
