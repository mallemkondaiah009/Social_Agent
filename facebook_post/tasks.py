import httpx
from celery import shared_task
from celery.utils.log import get_task_logger
from .models import ScheduledPost
from .client import facebook_post_sync




@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="social_agent.publish_scheduled_post",
)
def publish_scheduled_post(self, scheduled_post_id: int):
    try:
        post = ScheduledPost.objects.get(id=scheduled_post_id)
    except ScheduledPost.DoesNotExist:
        
        return

    if post.status != "pending":
        
        return

    try:
        status_code, result = facebook_post_sync(post.message, post.link)
    except (httpx.TimeoutException, httpx.RequestError) as exc:
      
        raise self.retry(exc=exc)

    if status_code == 200:
        post.status = "published"
        post.fb_post_id = result.get("id")
        post.save(update_fields=["status", "fb_post_id"])
       
        return {"status": "published", "fb_post_id": post.fb_post_id}

    post.status = "failed"
    post.error = str(result)
    post.save(update_fields=["status", "error"])
  
    return {"status": "failed", "error": result}