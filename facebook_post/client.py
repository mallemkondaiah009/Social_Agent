import httpx
from django.conf import settings

# Reused across all requests — one connection pool
_async_client = httpx.AsyncClient(timeout=10.0)
_sync_client = httpx.Client(timeout=10.0)


def _build_payload(message: str, link: str | None) -> tuple[str, dict, dict]:
    url = (
        f"https://graph.facebook.com"
        f"/{settings.FB_GRAPH_VERSION}"
        f"/{settings.FB_PAGE_ID}/feed"
    )
    payload = {"message": message}
    if link:
        payload["link"] = link

    headers = {"Authorization": f"Bearer {settings.FB_ACCESS_TOKEN}"}
    return url, payload, headers


async def facebook_post_async(message: str, link: str | None) -> tuple[int, dict]:
    """Used in async views."""
    url, payload, headers = _build_payload(message, link)
    response = await _async_client.post(url, data=payload, headers=headers)
    return response.status_code, response.json()


def facebook_post_sync(message: str, link: str | None) -> tuple[int, dict]:
    """Used in Celery tasks."""
    url, payload, headers = _build_payload(message, link)
    response = _sync_client.post(url, data=payload, headers=headers)
    return response.status_code, response.json()