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
    last_celery_task_id = models.CharField(max_length=100, blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["celery_task_id"]),
            models.Index(fields=["last_celery_task_id"]),
        ]

    def __str__(self):
        return f"Post #{self.id} - {self.status} - {self.scheduled_at}"


class ScheduledAd(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("publishing", "Publishing"),
        ("done", "Done"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    topic = models.CharField(max_length=255)
    primary_text = models.TextField()
    headline = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    link_url = models.URLField()
    image = models.FileField(upload_to="ads/", blank=True, null=True)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    daily_budget = models.PositiveIntegerField(default=10000)
    meta_campaign_id = models.CharField(max_length=100, blank=True, null=True)
    meta_adset_id = models.CharField(max_length=100, blank=True, null=True)
    meta_creative_id = models.CharField(max_length=100, blank=True, null=True)
    meta_ad_id = models.CharField(max_length=100, blank=True, null=True)
    meta_image_hash = models.CharField(max_length=100, blank=True, null=True)
    celery_task_id = models.CharField(max_length=100, blank=True, null=True)
    last_celery_task_id = models.CharField(max_length=100, blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_at"]
        indexes = [
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["celery_task_id"]),
        ]

    def __str__(self):
        return f"Ad #{self.id} - {self.status} - {self.scheduled_at}"
