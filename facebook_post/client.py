import httpx
from django.conf import settings
from django.core.files.storage import default_storage

# Reused across all requests — one connection pool
_async_client = httpx.AsyncClient(timeout=10.0)
_sync_client = httpx.Client(timeout=10.0)


def _build_payload(message: str, link: str | None, image_path: str | None = None) -> tuple[str, dict, dict, dict | None]:
    url = (
        f"https://graph.facebook.com"
        f"/{settings.FB_GRAPH_VERSION}"
        f"/{settings.FB_PAGE_ID}/feed"
    )
    payload = {"message": message}
    if link:
        payload["link"] = link

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
