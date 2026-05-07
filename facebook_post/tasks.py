from datetime import timedelta

import httpx
from celery import shared_task, uuid
from celery.utils.log import get_task_logger
from django.db.models import Q
from django.utils import timezone

from .models import ScheduledPost
from .client import facebook_post_sync


logger = get_task_logger(__name__)
STALE_PENDING_AFTER_MINUTES = 2
STALE_PUBLISHING_AFTER_MINUTES = 15


def enqueue_scheduled_post(scheduled_post_id: int) -> str | None:
    try:
        post = ScheduledPost.objects.get(id=scheduled_post_id)
    except ScheduledPost.DoesNotExist:
        logger.warning("Scheduled post %s does not exist.", scheduled_post_id)
        return None

    if post.status != "pending":
        logger.info("Skipping enqueue for scheduled post %s with status %s.", post.id, post.status)
        return None

    task_id = uuid()
    ScheduledPost.objects.filter(id=post.id, status="pending").update(celery_task_id=task_id)
    publish_scheduled_post.apply_async(args=[post.id], eta=post.scheduled_at, task_id=task_id)
    return task_id


@shared_task(name="social_agent.publish_due_scheduled_posts")
def publish_due_scheduled_posts(batch_size: int = 100):
    now = timezone.now()
    stale_pending_before = now - timedelta(minutes=STALE_PENDING_AFTER_MINUTES)
    stale_before = now - timedelta(minutes=STALE_PUBLISHING_AFTER_MINUTES)

    ScheduledPost.objects.filter(
        status="publishing",
        updated_at__lte=stale_before,
    ).update(status="pending", celery_task_id=None)

    post_ids = list(
        ScheduledPost.objects.filter(
            status="pending",
            scheduled_at__lte=now,
        )
        .filter(
            Q(celery_task_id__isnull=True)
            | Q(celery_task_id="")
            | Q(scheduled_at__lte=stale_pending_before)
        )
        .order_by("scheduled_at")
        .values_list("id", flat=True)[:batch_size]
    )

    queued = 0
    for post_id in post_ids:
        task_id = uuid()
        claimed = ScheduledPost.objects.filter(
            id=post_id,
            status="pending",
            scheduled_at__lte=timezone.now(),
        ).update(celery_task_id=task_id)

        if not claimed:
            continue

        publish_scheduled_post.apply_async(args=[post_id], task_id=task_id)
        queued += 1

    return {"queued": queued}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="social_agent.publish_scheduled_post",
)
def publish_scheduled_post(self, scheduled_post_id: int):
    task_id = self.request.id
    claimed = ScheduledPost.objects.filter(
        id=scheduled_post_id,
        celery_task_id=task_id,
        status__in=["pending", "publishing"],
    ).update(status="publishing")

    if not claimed:
        logger.info("Skipping scheduled post %s for task %s.", scheduled_post_id, task_id)
        return

    post = ScheduledPost.objects.get(id=scheduled_post_id)
    now = timezone.now()

    if post.scheduled_at > now:
        ScheduledPost.objects.filter(id=post.id, status="publishing").update(status="pending")
        publish_scheduled_post.apply_async(args=[post.id], eta=post.scheduled_at, task_id=task_id)
        logger.info(
            "Scheduled post %s ran early at %s; requeued for %s.",
            post.id,
            now,
            post.scheduled_at,
        )
        return

    try:
        status_code, result = facebook_post_sync(post.message, post.link)
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        raise self.retry(exc=exc)

    if status_code == 200:
        post.status = "published"
        post.fb_post_id = result.get("id")
        post.celery_task_id = None
        post.save(update_fields=["status", "fb_post_id", "celery_task_id", "updated_at"])

        return {"status": "published", "fb_post_id": post.fb_post_id}

    post.status = "failed"
    post.error = str(result)
    post.celery_task_id = None
    post.save(update_fields=["status", "error", "celery_task_id", "updated_at"])

    return {"status": "failed", "error": result}
