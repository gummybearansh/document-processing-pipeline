import pytest

from document_processing_pipeline.llm.gemini_client import GeminiClient


def test_parse_json_payload_accepts_plain_json_object():
    parsed = GeminiClient._parse_json_payload('{"a": 1, "b": "x"}')
    assert parsed == {"a": 1, "b": "x"}


def test_parse_json_payload_accepts_fenced_json():
    parsed = GeminiClient._parse_json_payload("```json\n{\"a\": 1}\n```")
    assert parsed == {"a": 1}


def test_parse_json_payload_extracts_embedded_json():
    parsed = GeminiClient._parse_json_payload('Here you go:\n{"a": 1}\nThanks!')
    assert parsed == {"a": 1}


def test_parse_json_payload_raises_on_missing_json_object():
    with pytest.raises(ValueError):
        GeminiClient._parse_json_payload("No JSON here")
