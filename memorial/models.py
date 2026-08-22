import uuid
from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

private_storage = FileSystemStorage(location=Path(settings.BASE_DIR) / "private_uploads")


def family_evidence_path(instance, filename):
    extension = Path(filename).suffix.lower()[:10]
    return f"family-evidence/{uuid.uuid4().hex}{extension}"

class Martyr(models.Model):
    source_id = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=255, db_index=True)
    normalized_name = models.CharField(max_length=255, db_index=True, blank=True)
    hometown = models.CharField(max_length=500, blank=True, db_index=True)
    birth_text = models.CharField(max_length=100, blank=True)
    death_text = models.CharField(max_length=100, blank=True)
    zone = models.CharField(max_length=30, blank=True, db_index=True)
    grave_row = models.CharField(max_length=30, blank=True)
    grave_number = models.CharField(max_length=30, blank=True)
    source_url = models.URLField(max_length=500)
    source_hash = models.CharField(max_length=64, blank=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["name", "source_id"]
        indexes = [models.Index(fields=["zone", "grave_row", "grave_number"])]

    def __str__(self):
        return self.name

class SyncRun(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    pages_processed = models.PositiveIntegerField(default=0)
    records_seen = models.PositiveIntegerField(default=0)
    records_created = models.PositiveIntegerField(default=0)
    records_updated = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default="running")
    message = models.TextField(blank=True)

class Tribute(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ duyệt"
        APPROVED = "approved", "Đã duyệt"
        REJECTED = "rejected", "Từ chối"

    martyr = models.ForeignKey(Martyr, on_delete=models.CASCADE, related_name="tributes")
    author_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    content = models.TextField(max_length=1000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    ip_hash = models.CharField(max_length=64, db_index=True, editable=False)
    user_agent = models.CharField(max_length=300, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["martyr", "status", "created_at"])]

    def __str__(self):
        return f"{self.author_name} → {self.martyr}"


class FamilySubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Chờ xác minh"
        CONTACTED = "contacted", "Đã liên hệ"
        VERIFIED = "verified", "Đã xác minh"
        REJECTED = "rejected", "Từ chối"

    martyr = models.ForeignKey(Martyr, on_delete=models.CASCADE, related_name="family_submissions")
    full_name = models.CharField(max_length=120)
    relationship = models.CharField(max_length=30)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    hometown = models.CharField(max_length=300, blank=True)
    message = models.TextField(max_length=3000)
    evidence = models.FileField(storage=private_storage, upload_to=family_evidence_path, blank=True, editable=False)
    allow_publication = models.BooleanField(default=False)
    consented_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    admin_note = models.TextField(blank=True)
    ip_hash = models.CharField(max_length=64, db_index=True, editable=False)
    user_agent = models.CharField(max_length=300, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["martyr", "status", "created_at"], name="family_martyr_status_idx")]

    def __str__(self):
        return f"{self.full_name} → {self.martyr}"


class TourPoint(models.Model):
    slug = models.SlugField(max_length=50, unique=True)
    number = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    x_percent = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    y_percent = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("number",)

    def __str__(self):
        return f"{self.number:02d} · {self.title}"


class TourConfiguration(models.Model):
    overview_image = models.FileField(upload_to="tour/", blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cấu hình trải nghiệm 360°"
        verbose_name_plural = "Cấu hình trải nghiệm 360°"

    def __str__(self):
        return "Ảnh tổng quan trải nghiệm 360°"

    @classmethod
    def load(cls):
        configuration, _ = cls.objects.get_or_create(pk=1)
        return configuration
