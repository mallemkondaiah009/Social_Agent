from rest_framework import serializers
from django.utils import timezone
from .models import ScheduledPost


class ScheduledPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledPost
        fields = [
            "id",
            "message",
            "link",
            "scheduled_at",
            "status",
            "fb_post_id",
            "error",
            "created_at",
        ]
        read_only_fields = ["status", "fb_post_id", "error", "created_at"]

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("scheduled_at must be a future date and time.")
        return value