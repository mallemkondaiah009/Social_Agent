from django.contrib import admin
from django.utils.html import format_html
from .models import ScheduledAd, ScheduledPost


@admin.register(ScheduledPost)
class ScheduledPostAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "message_preview",
        "status",
        "scheduled_at",
        "fb_post_id",
        "active_task_id_display",
        "last_task_id_display",
        "created_at",
        "updated_at",
    ]
    list_filter = ["status", "scheduled_at", "created_at", "updated_at"]
    search_fields = ["message", "fb_post_id", "celery_task_id", "last_celery_task_id"]
    readonly_fields = [
        "fb_post_id",
        "celery_task_id",
        "last_celery_task_id",
        "error",
        "created_at",
        "updated_at",
    ]
    fields = [
        "message",
        "link",
        "scheduled_at",
        "status",
        "fb_post_id",
        "celery_task_id",
        "last_celery_task_id",
        "error",
        "created_at",
        "updated_at",
    ]
    ordering = ["scheduled_at"]
    list_per_page = 50

    @admin.display(description="Message", ordering="message")
    def message_preview(self, obj):
        preview = obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
        return preview

    @admin.display(description="Active task ID", ordering="celery_task_id")
    def active_task_id_display(self, obj):
        return obj.celery_task_id or "-"

    @admin.display(description="Last task ID", ordering="last_celery_task_id")
    def last_task_id_display(self, obj):
        return obj.last_celery_task_id or "-"


@admin.register(ScheduledAd)
class ScheduledAdAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "topic",
        "status",
        "image_preview",
        "scheduled_at",
        "meta_campaign_id",
        "meta_adset_id",
        "meta_creative_id",
        "meta_ad_id",
        "active_task_id_display",
        "created_at",
    ]
    list_filter = ["status", "scheduled_at", "created_at", "updated_at"]
    search_fields = [
        "topic",
        "primary_text",
        "headline",
        "meta_campaign_id",
        "meta_adset_id",
        "meta_creative_id",
        "meta_ad_id",
        "celery_task_id",
        "last_celery_task_id",
    ]
    readonly_fields = [
        "meta_campaign_id",
        "meta_adset_id",
        "meta_creative_id",
        "meta_ad_id",
        "meta_image_hash",
        "celery_task_id",
        "last_celery_task_id",
        "error",
        "created_at",
        "updated_at",
        "image_display",
    ]
    fieldsets = (
        ("Ad Content", {
            "fields": ("topic", "primary_text", "headline", "description", "image", "image_display")
        }),
        ("Publishing Details", {
            "fields": ("link_url", "scheduled_at", "status", "daily_budget")
        }),
        ("Meta Ad Stack", {
            "fields": ("meta_campaign_id", "meta_adset_id", "meta_creative_id", "meta_ad_id", "meta_image_hash"),
            "classes": ("collapse",)
        }),
        ("Task Management", {
            "fields": ("celery_task_id", "last_celery_task_id", "error"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
    ordering = ["scheduled_at"]
    list_per_page = 50

    @admin.display(description="Image Preview", ordering="image")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 4px; object-fit: cover;" />',
                obj.image.url
            )
        return "-"

    @admin.display(description="Image Full View")
    def image_display(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="300" height="300" style="border-radius: 8px; object-fit: contain; max-width: 100%;" />',
                obj.image.url
            )
        return "No image uploaded"

    @admin.display(description="Active task ID", ordering="celery_task_id")
    def active_task_id_display(self, obj):
        return obj.celery_task_id or "-"

    @admin.display(description="Last task ID", ordering="last_celery_task_id")
    def last_task_id_display(self, obj):
        return obj.last_celery_task_id or "-"
