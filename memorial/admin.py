from pathlib import Path
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import path
from django.utils import timezone
from .models import FamilySubmission, Martyr, SyncRun, Tribute

@admin.register(Martyr)
class MartyrAdmin(admin.ModelAdmin):
    list_display = ("name", "hometown", "zone", "grave_row", "grave_number", "last_seen_at")
    search_fields = ("name", "normalized_name", "hometown")
    list_filter = ("zone", "is_verified")
    readonly_fields = ("source_id", "source_url", "source_hash", "first_seen_at", "last_seen_at")

admin.site.register(SyncRun)

@admin.action(description="Duyệt các lời tri ân đã chọn")
def approve_tributes(modeladmin, request, queryset):
    queryset.update(status=Tribute.Status.APPROVED, reviewed_at=timezone.now())

@admin.action(description="Từ chối các lời tri ân đã chọn")
def reject_tributes(modeladmin, request, queryset):
    queryset.update(status=Tribute.Status.REJECTED, reviewed_at=timezone.now())

@admin.register(Tribute)
class TributeAdmin(admin.ModelAdmin):
    list_display = ("author_name", "martyr", "masked_phone", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("author_name", "phone", "content", "martyr__name")
    readonly_fields = ("ip_hash", "user_agent", "created_at", "reviewed_at")
    actions = (approve_tributes, reject_tributes)

    @admin.display(description="Số điện thoại")
    def masked_phone(self, obj):
        return f"{obj.phone[:4]}***{obj.phone[-3:]}"


@admin.action(description="Đánh dấu đã liên hệ")
def mark_family_contacted(modeladmin, request, queryset):
    queryset.update(status=FamilySubmission.Status.CONTACTED, reviewed_at=timezone.now())


@admin.action(description="Đánh dấu đã xác minh")
def verify_family_submissions(modeladmin, request, queryset):
    queryset.update(status=FamilySubmission.Status.VERIFIED, reviewed_at=timezone.now())


@admin.register(FamilySubmission)
class FamilySubmissionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "martyr", "relationship", "phone", "email", "status", "created_at")
    list_filter = ("status", "relationship", "allow_publication", "created_at")
    search_fields = ("full_name", "phone", "email", "hometown", "message", "martyr__name")
    readonly_fields = ("martyr", "full_name", "relationship", "phone", "email", "hometown", "message",
                       "allow_publication", "consented_at", "evidence_download", "ip_hash", "user_agent",
                       "created_at", "reviewed_at")
    actions = (mark_family_contacted, verify_family_submissions)

    def get_urls(self):
        return [path("<int:object_id>/evidence/", self.admin_site.admin_view(self.download_evidence),
                     name="memorial_familysubmission_evidence")] + super().get_urls()

    def download_evidence(self, request, object_id):
        submission = self.get_object(request, object_id)
        if not submission or not submission.evidence:
            raise Http404
        return FileResponse(submission.evidence.open("rb"), as_attachment=True,
                            filename=Path(submission.evidence.name).name)

    @admin.display(description="Tệp xác minh riêng tư")
    def evidence_download(self, obj):
        if not obj or not obj.evidence:
            return "Không có"
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse("admin:memorial_familysubmission_evidence", args=[obj.pk])
        return format_html('<a href="{}">Tải tệp xác minh</a>', url)
