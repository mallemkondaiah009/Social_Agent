from django.contrib import admin
from .models import ScheduledAd, ScheduledPost


@admin.register(ScheduledPost)
class ScheduledPostAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "message",
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
        "scheduled_at",
        "meta_campaign_id",
        "meta_adset_id",
        "meta_creative_id",
        "meta_ad_id",
        "active_task_id_display",
        "last_task_id_display",
        "created_at",
        "updated_at",
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
    ]
    fields = [
        "topic",
        "primary_text",
        "headline",
        "description",
        "link_url",
        "image",
        "scheduled_at",
        "status",
        "daily_budget",
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
    ]
    ordering = ["scheduled_at"]
    list_per_page = 50

    @admin.display(description="Active task ID", ordering="celery_task_id")
    def active_task_id_display(self, obj):
        return obj.celery_task_id or "-"

    @admin.display(description="Last task ID", ordering="last_celery_task_id")
    def last_task_id_display(self, obj):
        return obj.last_celery_task_id or "-"
