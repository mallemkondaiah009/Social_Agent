from uuid import uuid4

from adrf.views import APIView
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.response import Response
from rest_framework import status

from .services.agent import AgentService, AgentServiceError
from .models import ScheduledAd, ScheduledPost
from .serializers import (
    GenerateScheduledPostSerializer,
    ScheduleAdSerializer,
    ScheduledAdSerializer,
    ScheduledPostSerializer,
)
from .services.facebook_posts import (
    get_scheduled_post,
    get_all_posts,
    cancel_post,
)
from .tasks import enqueue_scheduled_post, generate_scheduled_post, generate_scheduled_ad
from asgiref.sync import sync_to_async
from celery import uuid


class SchedulePostView(APIView):
    async def post(self, request):
        serializer = ScheduledPostSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        post = await serializer.asave()
        await sync_to_async(enqueue_scheduled_post)(post.id)

        return Response(
            {
                "message": "Post scheduled successfully.",
                "post": await ScheduledPostSerializer(post).adata,
            },
            status=status.HTTP_201_CREATED,
        )


class GeneratePostView(APIView):
    async def post(self, request):
        serializer = GenerateScheduledPostSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        topic = serializer.validated_data["topic"]
        scheduled_time = serializer.validated_data["scheduled_time"]

        # Create post with "generating" status
        post = await ScheduledPost.objects.acreate(
            message=topic,  # Store topic temporarily, will be replaced with generated content
            scheduled_at=scheduled_time,
            status="generating",
        )

        # Trigger background generation task
        task_id = str(uuid())
        await sync_to_async(generate_scheduled_post.apply_async)(
            args=[post.id],
            task_id=task_id,
        )

        return Response(
            {
                "message": "Post generation started in background.",
                "topic": topic,
                "post": await ScheduledPostSerializer(post).adata,
            },
            status=status.HTTP_201_CREATED,
        )


class ScheduleAdView(APIView):
    async def post(self, request):
        serializer = ScheduleAdSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        topic = serializer.validated_data["topic"]
        scheduled_time = serializer.validated_data["scheduled_time"]
        link_url = serializer.validated_data["link_url"]
        daily_budget = serializer.validated_data.get(
            "daily_budget",
            settings.META_AD_DEFAULT_DAILY_BUDGET,
        )

        # Create ad with "generating" status and placeholder values
        ad = await ScheduledAd.objects.acreate(
            topic=topic,
            primary_text="Generating...",
            headline="Generating...",
            description="Generating...",
            link_url=link_url,
            scheduled_at=scheduled_time,
            daily_budget=daily_budget,
            status="generating",
        )

        # Trigger background generation task
        task_id = str(uuid())
        await sync_to_async(generate_scheduled_ad.apply_async)(
            args=[ad.id],
            task_id=task_id,
        )

        return Response(
            {
                "message": "Ad generation started in background.",
                "ad": await ScheduledAdSerializer(ad).adata,
            },
            status=status.HTTP_201_CREATED,
        )


class ScheduledPostListView(APIView):
    """List all scheduled posts."""

    async def get(self, request):
        posts = await get_all_posts()
        serializer = ScheduledPostSerializer(posts, many=True)
        return Response(await serializer.adata)


class ScheduledPostDetailView(APIView):
    """Retrieve a single scheduled post."""

    async def get(self, request, post_id: int):
        post = await get_scheduled_post(post_id)
        if not post:
            return Response(
                {"error": "Post not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(await ScheduledPostSerializer(post).adata)


class CancelScheduledPostView(APIView):
    """Cancel a pending scheduled post."""

    async def patch(self, request, post_id: int):
        post = await get_scheduled_post(post_id)
        if not post:
            return Response(
                {"error": "Post not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if post.status != "pending":
            return Response(
                {"error": f"Cannot cancel a {post.status} post."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        await cancel_post(post)
        return Response({"message": "Post cancelled successfully."})
