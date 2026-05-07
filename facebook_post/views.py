from adrf.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import ScheduledPostSerializer
from .services import (
    get_scheduled_post,
    get_all_posts,
    cancel_post,
)
from .tasks import enqueue_scheduled_post
from asgiref.sync import sync_to_async


class SchedulePostView(APIView):
    async def post(self, request):
        serializer = ScheduledPostSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        post = await sync_to_async(serializer.save)()
        await sync_to_async(enqueue_scheduled_post)(post.id)

        return Response(
            {
                "message": "Post scheduled successfully.",
                "post": ScheduledPostSerializer(post).data,
            },
            status=status.HTTP_201_CREATED,
        )


class ScheduledPostListView(APIView):
    """List all scheduled posts."""

    async def get(self, request):
        posts = await get_all_posts()
        serializer = ScheduledPostSerializer(posts, many=True)
        return Response(serializer.data)


class ScheduledPostDetailView(APIView):
    """Retrieve a single scheduled post."""

    async def get(self, request, post_id: int):
        post = await get_scheduled_post(post_id)
        if not post:
            return Response(
                {"error": "Post not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ScheduledPostSerializer(post).data)


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
