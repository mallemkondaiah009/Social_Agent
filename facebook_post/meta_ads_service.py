import json
from pathlib import Path

import httpx
from django.conf import settings

from .models import ScheduledAd


class MetaAdsServiceError(Exception):
    """Raised when Meta ad creation fails."""


class MetaAdsService:
    def __init__(self):
        self.base_url = f"https://graph.facebook.com/{settings.FB_GRAPH_VERSION}"
        self.access_token = settings.FB_ACCESS_TOKEN
        self.page_id = settings.FB_PAGE_ID
        self.ad_account_id = self._normalize_ad_account_id(settings.META_AD_ACCOUNT_ID)

        if not self.access_token:
            raise MetaAdsServiceError("FB_ACCESS_TOKEN is not configured.")
        if not self.page_id:
            raise MetaAdsServiceError("FB_PAGE_ID is not configured.")
        if not self.ad_account_id:
            raise MetaAdsServiceError("META_AD_ACCOUNT_ID is not configured.")

    def create_ad_stack(self, ad: ScheduledAd) -> dict:
        with httpx.Client(timeout=60.0) as client:
            campaign_id = self._create_campaign(client, ad)
            adset_id = self._create_adset(client, ad, campaign_id)
            image_hash = self._upload_image(client, ad)
            creative_id = self._create_creative(client, ad, image_hash)
            meta_ad_id = self._create_ad(client, ad, adset_id, creative_id)

        return {
            "meta_campaign_id": campaign_id,
            "meta_adset_id": adset_id,
            "meta_image_hash": image_hash,
            "meta_creative_id": creative_id,
            "meta_ad_id": meta_ad_id,
        }

    def _create_campaign(self, client: httpx.Client, ad: ScheduledAd) -> str:
        response = client.post(
            f"{self.base_url}/{self.ad_account_id}/campaigns",
            data={
                "access_token": self.access_token,
                "name": f"Social Agent - {ad.topic}",
                "objective": "OUTCOME_TRAFFIC",
                "status": settings.META_AD_DEFAULT_STATUS,
                "special_ad_categories": json.dumps([]),
                "is_adset_budget_sharing_enabled": "false",
            },
        )
        return self._id_from_response(response, "campaign")

    def _create_adset(self, client: httpx.Client, ad: ScheduledAd, campaign_id: str) -> str:
        response = client.post(
            f"{self.base_url}/{self.ad_account_id}/adsets",
            data={
                "access_token": self.access_token,
                "name": f"Social Agent Ad Set - {ad.topic}",
                "campaign_id": campaign_id,
                "daily_budget": str(ad.daily_budget),
                "billing_event": "IMPRESSIONS",
                "optimization_goal": "LINK_CLICKS",
                "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                "targeting": json.dumps(
                    {
                        "geo_locations": {
                            "countries": [settings.META_AD_DEFAULT_COUNTRY],
                        },
                    }
                ),
                "status": settings.META_AD_DEFAULT_STATUS,
            },
        )
        return self._id_from_response(response, "ad set")

    def _upload_image(self, client: httpx.Client, ad: ScheduledAd) -> str:
        if not ad.image:
            raise MetaAdsServiceError("Scheduled ad does not have a generated image.")

        image_path = Path(ad.image.path)
        with image_path.open("rb") as image_file:
            response = client.post(
                f"{self.base_url}/{self.ad_account_id}/adimages",
                data={"access_token": self.access_token},
                files={"filename": (image_path.name, image_file, "image/png")},
            )

        response_data = self._json_response(response, "ad image")
        images = response_data.get("images", {})
        for image_info in images.values():
            image_hash = image_info.get("hash")
            if image_hash:
                return image_hash

        raise MetaAdsServiceError(f"Meta ad image response missing hash: {response_data}")

    def _create_creative(self, client: httpx.Client, ad: ScheduledAd, image_hash: str) -> str:
        object_story_spec = {
            "page_id": self.page_id,
            "link_data": {
                "message": ad.primary_text,
                "link": ad.link_url,
                "name": ad.headline,
                "description": ad.description or "",
                "image_hash": image_hash,
                "call_to_action": {
                    "type": "LEARN_MORE",
                    "value": {"link": ad.link_url},
                },
            },
        }
        response = client.post(
            f"{self.base_url}/{self.ad_account_id}/adcreatives",
            data={
                "access_token": self.access_token,
                "name": f"Social Agent Creative - {ad.topic}",
                "object_story_spec": json.dumps(object_story_spec),
            },
        )
        return self._id_from_response(response, "ad creative")

    def _create_ad(
        self,
        client: httpx.Client,
        ad: ScheduledAd,
        adset_id: str,
        creative_id: str,
    ) -> str:
        response = client.post(
            f"{self.base_url}/{self.ad_account_id}/ads",
            data={
                "access_token": self.access_token,
                "name": f"Social Agent Ad - {ad.topic}",
                "adset_id": adset_id,
                "creative": json.dumps({"creative_id": creative_id}),
                "status": settings.META_AD_DEFAULT_STATUS,
            },
        )
        return self._id_from_response(response, "ad")

    def _id_from_response(self, response: httpx.Response, resource_name: str) -> str:
        response_data = self._json_response(response, resource_name)
        resource_id = response_data.get("id")
        if not resource_id:
            raise MetaAdsServiceError(f"Meta {resource_name} response missing id: {response_data}")
        return resource_id

    def _json_response(self, response: httpx.Response, resource_name: str) -> dict:
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise MetaAdsServiceError(f"Meta {resource_name} API error: {exc.response.text}") from exc
        except ValueError as exc:
            raise MetaAdsServiceError(f"Meta {resource_name} response was not JSON.") from exc

    def _normalize_ad_account_id(self, ad_account_id: str | None) -> str | None:
        if not ad_account_id:
            return None
        if ad_account_id.startswith("act_"):
            return ad_account_id
        return f"act_{ad_account_id}"
