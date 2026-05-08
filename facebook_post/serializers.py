from adrf.serializers import ModelSerializer
from adrf.serializers import Serializer
from rest_framework import serializers
from django.utils import timezone
from .models import ScheduledAd, ScheduledPost


class ScheduledPostSerializer(ModelSerializer):
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


class GenerateScheduledPostSerializer(Serializer):
    topic = serializers.CharField(max_length=255)
    scheduled_time = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M", "iso-8601"])

    def validate_scheduled_time(self, value):
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())

        if value <= timezone.now():
            raise serializers.ValidationError("scheduled_time must be a future date and time.")

        return value


class ScheduledAdSerializer(ModelSerializer):
    class Meta:
        model = ScheduledAd
        fields = [
            "id",
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
            "error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "primary_text",
            "headline",
            "description",
            "image",
            "status",
            "meta_campaign_id",
            "meta_adset_id",
            "meta_creative_id",
            "meta_ad_id",
            "meta_image_hash",
            "error",
            "created_at",
            "updated_at",
        ]


class ScheduleAdSerializer(Serializer):
    topic = serializers.CharField(max_length=255)
    scheduled_time = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M", "iso-8601"])
    link_url = serializers.URLField()
    daily_budget = serializers.IntegerField(required=False, min_value=100)

    def validate_scheduled_time(self, value):
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())

        if value <= timezone.now():
            raise serializers.ValidationError("scheduled_time must be a future date and time.")

        return value
