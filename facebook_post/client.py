import httpx
from django.conf import settings
from django.core.files.storage import default_storage

# Reused across all requests — one connection pool
_async_client = httpx.AsyncClient(timeout=30.0)
_sync_client = httpx.Client(timeout=30.0)


<<<<<<< HEAD
def _feed_url() -> str:
    """Build the Page feed endpoint URL."""
    return (
=======
def _build_payload(message: str, link: str | None, image_path: str | None = None) -> tuple[str, dict, dict, dict | None]:
    url = (
>>>>>>> 52a29708f1e89e709676197d7f6c5d1819c193e9
        f"https://graph.facebook.com"
        f"/{settings.FB_GRAPH_VERSION}"
        f"/{settings.FB_PAGE_ID}/feed"
    )


def _photos_url() -> str:
    """Build the Page photos endpoint URL."""
    return (
        f"https://graph.facebook.com"
        f"/{settings.FB_GRAPH_VERSION}"
        f"/{settings.FB_PAGE_ID}/photos"
    )


def _auth_headers() -> dict:
    """Return the Bearer auth header."""
    return {"Authorization": f"Bearer {settings.FB_ACCESS_TOKEN}"}


# ---------------------------------------------------------------------------
# Async variants
# ---------------------------------------------------------------------------

async def _upload_photo_async(image_bytes: bytes) -> str:
    """Upload an image as unpublished and return its media_fbid.

    Args:
        image_bytes: Raw bytes of the image to upload.

    Returns:
        The ``id`` (media_fbid) of the unpublished photo object.

    Raises:
        httpx.HTTPStatusError: If the Graph API returns a non-2xx response.
    """
    response = await _async_client.post(
        _photos_url(),
        data={"published": "false", "access_token": settings.FB_ACCESS_TOKEN},
        files={"source": ("image.png", image_bytes, "image/png")},
    )
    response.raise_for_status()
    return response.json()["id"]


async def facebook_post_async(
    message: str,
    link: str | None = None,
    image_bytes: bytes | None = None,
) -> tuple[int, dict]:
    """Publish a Facebook Page post, optionally with an attached image.

    When ``image_bytes`` is provided the photo is first uploaded as an
    unpublished object (so it does not appear on its own in the feed) and
    then attached to the feed post via ``attached_media``.

    Args:
        message: The post body text.
        link: An optional URL to attach as a link preview.
        image_bytes: Raw image bytes to attach to the post.

    Returns:
        A tuple of (HTTP status code, parsed JSON response body).
    """
    payload: dict = {"message": message}
    if link:
        payload["link"] = link

<<<<<<< HEAD
    if image_bytes:
        media_fbid = await _upload_photo_async(image_bytes)
        payload["attached_media"] = f'[{{"media_fbid":"{media_fbid}"}}]'

    response = await _async_client.post(
        _feed_url(),
        data=payload,
        headers=_auth_headers(),
    )
    return response.status_code, response.json()


# ---------------------------------------------------------------------------
# Sync variants (used by Celery tasks)
# ---------------------------------------------------------------------------

def _upload_photo_sync(image_bytes: bytes) -> str:
    """Upload an image as unpublished and return its media_fbid.

    Args:
        image_bytes: Raw bytes of the image to upload.

    Returns:
        The ``id`` (media_fbid) of the unpublished photo object.

    Raises:
        httpx.HTTPStatusError: If the Graph API returns a non-2xx response.
    """
    response = _sync_client.post(
        _photos_url(),
        data={"published": "false", "access_token": settings.FB_ACCESS_TOKEN},
        files={"source": ("image.png", image_bytes, "image/png")},
    )
    response.raise_for_status()
    return response.json()["id"]


def facebook_post_sync(
    message: str,
    link: str | None = None,
    image_bytes: bytes | None = None,
) -> tuple[int, dict]:
    """Publish a Facebook Page post, optionally with an attached image.

    When ``image_bytes`` is provided the photo is first uploaded as an
    unpublished object and then attached to the feed post via
    ``attached_media``.

    Args:
        message: The post body text.
        link: An optional URL to attach as a link preview.
        image_bytes: Raw image bytes to attach to the post.

    Returns:
        A tuple of (HTTP status code, parsed JSON response body).
    """
    payload: dict = {"message": message}
    if link:
        payload["link"] = link

    if image_bytes:
        media_fbid = _upload_photo_sync(image_bytes)
        payload["attached_media"] = f'[{{"media_fbid":"{media_fbid}"}}]'

    response = _sync_client.post(
        _feed_url(),
        data=payload,
        headers=_auth_headers(),
    )
    return response.status_code, response.json()
=======
    headers = {"Authorization": f"Bearer {settings.FB_ACCESS_TOKEN}"}
    
    # Handle image upload
    files = None
    if image_path:
        try:
            # Read image from storage
            image_file = default_storage.open(image_path, 'rb')
            files = {"source": image_file}
        except Exception:
            # If image doesn't exist, continue without it
            pass
    
    return url, payload, headers, files


async def facebook_post_async(message: str, link: str | None, image_path: str | None = None) -> tuple[int, dict]:
    """Used in async views."""
    url, payload, headers, files = _build_payload(message, link, image_path)
    response = await _async_client.post(url, data=payload, headers=headers, files=files)
    return response.status_code, response.json()


def facebook_post_sync(message: str, link: str | None, image_path: str | None = None) -> tuple[int, dict]:
    """Used in Celery tasks."""
    url, payload, headers, files = _build_payload(message, link, image_path)
    response = _sync_client.post(url, data=payload, headers=headers, files=files)
    return response.status_code, response.json()
>>>>>>> 52a29708f1e89e709676197d7f6c5d1819c193e9
