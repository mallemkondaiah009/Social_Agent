import base64
import json
from pathlib import Path

import httpx
from asgiref.sync import sync_to_async
from django.conf import settings


class AgentServiceError(Exception):
    """Raised when generated post content cannot be created."""


class AgentService:
    prompt_path = Path(settings.BASE_DIR) / "prompts" / "marketing" / "marketing-content-creator.md"

    async def generate_facebook_post(self, topic: str) -> str:
        prompt = await self._read_prompt()
        response_data = await self._create_response(
            prompt=prompt,
            user_input=(
                "Create one concise Facebook marketing post for this topic. "
                "Return only the final post text, with no labels or explanation.\n\n"
                f"Topic: {topic}"
            ),
        )
        return self._extract_text(response_data)

    async def generate_facebook_ad(self, topic: str) -> dict:
        prompt = await self._read_prompt()
        response_data = await self._create_response(
            prompt=prompt,
            user_input=(
                "Create Meta/Facebook ad copy for this topic. Return strict JSON only "
                "with keys: primary_text, headline, description, image_prompt. "
                "The image_prompt should describe a square ad image with no embedded text.\n\n"
                f"Topic: {topic}"
            ),
        )
        ad_content = self._extract_json(response_data)
        image_bytes = await self._create_image(ad_content["image_prompt"])
        ad_content["image_bytes"] = image_bytes
        return ad_content

    async def _read_prompt(self) -> str:
        try:
            return await sync_to_async(self.prompt_path.read_text)(encoding="utf-8")
        except OSError as exc:
            raise AgentServiceError(f"Prompt file not found: {self.prompt_path}") from exc

    async def _create_response(self, prompt: str, user_input: str) -> dict:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise AgentServiceError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": settings.OPENAI_MODEL,
            "instructions": prompt,
            "input": user_input,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            raise AgentServiceError(f"OpenAI API error: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            raise AgentServiceError(f"OpenAI request failed: {exc}") from exc

    async def _create_image(self, prompt: str) -> bytes:
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise AgentServiceError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": settings.OPENAI_IMAGE_MODEL,
            "prompt": prompt,
            "size": "1024x1024",
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                response_data = response.json()

                image_data = response_data.get("data", [{}])[0]
                if image_data.get("b64_json"):
                    return base64.b64decode(image_data["b64_json"])

                if image_data.get("url"):
                    image_response = await client.get(image_data["url"])
                    image_response.raise_for_status()
                    return image_response.content
        except httpx.HTTPStatusError as exc:
            raise AgentServiceError(f"OpenAI image API error: {exc.response.text}") from exc
        except httpx.RequestError as exc:
            raise AgentServiceError(f"OpenAI image request failed: {exc}") from exc

        raise AgentServiceError("OpenAI image response did not include image data.")

    def _extract_text(self, response_data: dict) -> str:
        output_text = response_data.get("output_text")
        if output_text:
            return output_text.strip()

        for item in response_data.get("output", []):
            if item.get("type") != "message":
                continue

            for content in item.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    return content["text"].strip()

        raise AgentServiceError("OpenAI response did not include generated text.")

    def _extract_json(self, response_data: dict) -> dict:
        text = self._extract_text(response_data)
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AgentServiceError("OpenAI response did not include valid ad JSON.") from exc

        required_fields = ["primary_text", "headline", "description", "image_prompt"]
        missing_fields = [field for field in required_fields if not parsed.get(field)]
        if missing_fields:
            raise AgentServiceError(f"OpenAI ad JSON missing fields: {', '.join(missing_fields)}")

        return parsed
