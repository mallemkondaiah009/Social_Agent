from datetime import timedelta
from uuid import uuid4

import httpx
from celery import shared_task, uuid
from celery.utils.log import get_task_logger
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Q
from django.utils import timezone

from .models import ScheduledAd, ScheduledPost
from .client import facebook_post_sync
from .services.meta_ads import MetaAdsService, MetaAdsServiceError
from .services.agent import AgentService, AgentServiceError


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
    ScheduledPost.objects.filter(id=post.id, status="pending").update(
        celery_task_id=task_id,
        last_celery_task_id=task_id,
    )
    publish_scheduled_post.apply_async(args=[post.id], eta=post.scheduled_at, task_id=task_id)
    return task_id


@shared_task(name="social_agent.generate_scheduled_post", bind=True, max_retries=3)
def generate_scheduled_post(self, scheduled_post_id: int):
    """Generate Facebook post content in background."""
    try:
        post = ScheduledPost.objects.get(id=scheduled_post_id, status="generating")
    except ScheduledPost.DoesNotExist:
        logger.warning("Scheduled post %s does not exist or is not in generating status.", scheduled_post_id)
        return

    try:
        generated_message = AgentService().generate_facebook_post(post.message)
        
        post.message = generated_message
        post.status = "pending"
        post.save(update_fields=["message", "status", "updated_at"])
        
        logger.info("Post %s generated successfully.", post.id)
        return {"status": "generated", "post_id": post.id}
        
    except AgentServiceError as exc:
        logger.error("Failed to generate post %s: %s", scheduled_post_id, str(exc))
        post.status = "failed"
        post.error = str(exc)
        post.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": str(exc)}
    except Exception as exc:
        logger.error("Unexpected error generating post %s: %s", scheduled_post_id, str(exc))
        raise self.retry(exc=exc, countdown=60)


@shared_task(name="social_agent.generate_scheduled_ad", bind=True, max_retries=3)
def generate_scheduled_ad(self, scheduled_ad_id: int):
    """Generate Facebook ad content and image in background."""
    try:
        ad = ScheduledAd.objects.get(id=scheduled_ad_id, status="generating")
    except ScheduledAd.DoesNotExist:
        logger.warning("Scheduled ad %s does not exist or is not in generating status.", scheduled_ad_id)
        return

    try:
        ad_content = AgentService().generate_facebook_ad(ad.topic)
        
        # Save image
        image_path = f"ads/generated/{uuid4()}.png"
        saved_image_path = default_storage.save(
            image_path,
            ContentFile(ad_content["image_bytes"]),
        )
        
        # Update ad with generated content
        ad.primary_text = ad_content["primary_text"]
        ad.headline = ad_content["headline"][:255]
        ad.description = ad_content["description"]
        ad.image = saved_image_path
        ad.status = "pending"
        ad.save(update_fields=["primary_text", "headline", "description", "image", "status", "updated_at"])
        
        logger.info("Ad %s generated successfully.", ad.id)
        return {"status": "generated", "ad_id": ad.id}
        
    except AgentServiceError as exc:
        logger.error("Failed to generate ad %s: %s", scheduled_ad_id, str(exc))
        ad.status = "failed"
        ad.error = str(exc)
        ad.save(update_fields=["status", "error", "updated_at"])
        return {"status": "failed", "error": str(exc)}
    except Exception as exc:
        logger.error("Unexpected error generating ad %s: %s", scheduled_ad_id, str(exc))
        raise self.retry(exc=exc, countdown=60)


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
        ).update(
            celery_task_id=task_id,
            last_celery_task_id=task_id,
        )

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


@shared_task(name="social_agent.publish_due_scheduled_ads")
def publish_due_scheduled_ads(batch_size: int = 50):
    now = timezone.now()
    stale_before = now - timedelta(minutes=STALE_PUBLISHING_AFTER_MINUTES)

    ScheduledAd.objects.filter(
        status="publishing",
        updated_at__lte=stale_before,
    ).update(status="pending", celery_task_id=None)

    ad_ids = list(
        ScheduledAd.objects.filter(
            status="pending",
            scheduled_at__lte=now,
        )
        .order_by("scheduled_at")
        .values_list("id", flat=True)[:batch_size]
    )

    queued = 0
    for ad_id in ad_ids:
        task_id = uuid()
        claimed = ScheduledAd.objects.filter(
            id=ad_id,
            status="pending",
            scheduled_at__lte=timezone.now(),
        ).update(
            status="publishing",
            celery_task_id=task_id,
            last_celery_task_id=task_id,
        )

        if not claimed:
            continue

        publish_scheduled_ad.apply_async(args=[ad_id], task_id=task_id)
        queued += 1

    return {"queued": queued}


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="social_agent.publish_scheduled_ad",
)
def publish_scheduled_ad(self, scheduled_ad_id: int):
    task_id = self.request.id
    try:
        ad = ScheduledAd.objects.get(
            id=scheduled_ad_id,
            celery_task_id=task_id,
            status="publishing",
        )
    except ScheduledAd.DoesNotExist:
        logger.info("Skipping scheduled ad %s for task %s.", scheduled_ad_id, task_id)
        return

    if ad.scheduled_at > timezone.now():
        ScheduledAd.objects.filter(id=ad.id, status="publishing").update(status="pending")
        logger.info("Scheduled ad %s ran before its scheduled time.", ad.id)
        return

    try:
        meta_ids = MetaAdsService().create_ad_stack(ad)
    except httpx.RequestError as exc:
        raise self.retry(exc=exc)
    except MetaAdsServiceError as exc:
        ad.status = "failed"
        ad.error = str(exc)
        ad.celery_task_id = None
        ad.save(update_fields=["status", "error", "celery_task_id", "updated_at"])
        return {"status": "failed", "error": str(exc)}

    ad.status = "done"
    ad.meta_campaign_id = meta_ids["meta_campaign_id"]
    ad.meta_adset_id = meta_ids["meta_adset_id"]
    ad.meta_creative_id = meta_ids["meta_creative_id"]
    ad.meta_ad_id = meta_ids["meta_ad_id"]
    ad.meta_image_hash = meta_ids["meta_image_hash"]
    ad.celery_task_id = None
    ad.save(
        update_fields=[
            "status",
            "meta_campaign_id",
            "meta_adset_id",
            "meta_creative_id",
            "meta_ad_id",
            "meta_image_hash",
            "celery_task_id",
            "updated_at",
        ]
    )

    return {"status": "done", **meta_ids}
