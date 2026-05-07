from django.db import models


class ScheduledPost(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("publishing", "Publishing"),
        ("published", "Published"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    message = models.TextField()
    link = models.URLField(blank=True, null=True)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    fb_post_id = models.CharField(max_length=100, blank=True, null=True)
    celery_task_id = models.CharField(max_length=100, blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["celery_task_id"]),
        ]

    def __str__(self):
        return f"Post #{self.id} - {self.status} - {self.scheduled_at}"
