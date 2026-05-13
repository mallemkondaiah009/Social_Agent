import logging
from ..models import ScheduledPost




async def get_scheduled_post(scheduled_post_id: int) -> ScheduledPost | None:
    try:
        return await ScheduledPost.objects.aget(id=scheduled_post_id)
    except ScheduledPost.DoesNotExist:
        
        return None


async def mark_post_published(post: ScheduledPost, fb_post_id: str):
    post.status = "published"
    post.fb_post_id = fb_post_id
    await post.asave(update_fields=["status", "fb_post_id"])
    

async def mark_post_failed(post: ScheduledPost, error: dict):
    post.status = "failed"
    post.error = str(error)
    await post.asave(update_fields=["status", "error"])
  


async def cancel_post(post: ScheduledPost):
    post.status = "cancelled"
    post.celery_task_id = None
    await post.asave(update_fields=["status", "celery_task_id"])
    


async def get_all_posts() -> list[ScheduledPost]:
    return [post async for post in ScheduledPost.objects.all()]


