import memorial.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("memorial", "0004_tourconfiguration")]

    operations = [
        migrations.CreateModel(
            name="FamilySubmission",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=120)),
                ("relationship", models.CharField(max_length=30)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("hometown", models.CharField(blank=True, max_length=300)),
                ("message", models.TextField(max_length=3000)),
                ("evidence", models.FileField(blank=True, editable=False, storage=memorial.models.private_storage, upload_to=memorial.models.family_evidence_path)),
                ("allow_publication", models.BooleanField(default=False)),
                ("consented_at", models.DateTimeField()),
                ("status", models.CharField(choices=[("pending", "Chờ xác minh"), ("contacted", "Đã liên hệ"), ("verified", "Đã xác minh"), ("rejected", "Từ chối")], db_index=True, default="pending", max_length=20)),
                ("admin_note", models.TextField(blank=True)),
                ("ip_hash", models.CharField(db_index=True, editable=False, max_length=64)),
                ("user_agent", models.CharField(blank=True, editable=False, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("martyr", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="family_submissions", to="memorial.martyr")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="familysubmission",
            index=models.Index(fields=["martyr", "status", "created_at"], name="family_martyr_status_idx"),
        ),
    ]
