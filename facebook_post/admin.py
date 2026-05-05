from django.contrib import admin
from .models import ScheduledPost


@admin.register(ScheduledPost)
class ScheduledPostAdmin(admin.ModelAdmin):
    list_display = ["id", "message", "status", "scheduled_at", "fb_post_id", "created_at"]
    list_filter = ["status"]
    search_fields = ["message", "fb_post_id"]
    readonly_fields = ["fb_post_id", "error", "created_at"]
    ordering = ["scheduled_at"]