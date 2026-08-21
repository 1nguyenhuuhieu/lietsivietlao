from django.db import models

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

