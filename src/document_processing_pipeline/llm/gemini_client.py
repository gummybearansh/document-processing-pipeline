from __future__ import annotations

import json
import re
from typing import Any

from document_processing_pipeline.config import settings
from google import genai
from google.genai import types


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key if api_key is not None else settings.gemini_api_key
        self._model = model if model is not None else settings.gemini_model
        self._client = genai.Client(api_key=self._api_key) if self._api_key else None

    @staticmethod
    def _parse_json_payload(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Expected top-level JSON object")
        except (json.JSONDecodeError, ValueError):
            decoder = json.JSONDecoder()
            for idx, char in enumerate(cleaned):
                if char not in "{[":
                    continue
                try:
                    parsed, _ = decoder.raw_decode(cleaned[idx:])
                    if isinstance(parsed, dict):
                        return parsed
                except json.JSONDecodeError:
                    continue
            raise ValueError("Model response did not contain a valid JSON object")

    def generate_json(
        self,
        prompt: str,
        media_parts: list[tuple[bytes, str]] | None = None,
    ) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("Gemini API key not configured")

        contents: list[Any] = [prompt]
        for data, mime_type in media_parts or []:
            contents.append(types.Part.from_bytes(data=data, mime_type=mime_type))

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=contents,
                config={
                    "temperature": 0,
                    "response_mime_type": "application/json",
                },
            )
            text = response.text or "{}"
            return self._parse_json_payload(text)
        except Exception:
            # Fail soft so the pipeline can still return partial structured output.
            return {}
