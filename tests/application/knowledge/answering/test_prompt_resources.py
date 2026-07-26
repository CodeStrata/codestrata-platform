"""Tests for externalized grounded-answer prompt resources (Phase 5.8.1)."""

from __future__ import annotations

import json
from importlib.resources import files
from unittest.mock import MagicMock

import pytest

from aimf.application.knowledge.answering.bedrock import BedrockAnswerProvider
from aimf.application.knowledge.answering.openai_provider import OpenAIAnswerProvider
from aimf.application.knowledge.answering.prompts import (
    DEFAULT_PROMPT_NAME,
    DEFAULT_PROMPT_VERSION,
    PROMPT_VERSION,
    PromptResourceError,
    build_repair_prompt,
    build_user_prompt,
    clear_prompt_cache,
    get_system_prompt,
    load_prompt_bundle,
    prompt_resource_root,
    prompt_version_path,
    render_template,
)
from aimf.application.knowledge.answering.protocol import AnswerProviderRequest
from aimf.domain.knowledge.answering import AnswerStyle
from aimf.domain.knowledge.retrieval import RetrievalHit


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    clear_prompt_cache()
    yield
    clear_prompt_cache()


def _hit() -> RetrievalHit:
    return RetrievalHit(
        rank=1,
        score=0.9,
        record_id="rec-1",
        citation_label="SRC-1",
        content="OwnersController handles owners.",
        source_type="code",
        file_path="OwnersController.java",
    )


def test_successful_loading() -> None:
    bundle = load_prompt_bundle()
    assert bundle.metadata.name == DEFAULT_PROMPT_NAME
    assert bundle.metadata.version == DEFAULT_PROMPT_VERSION
    assert bundle.metadata.response_schema_version == "1.0.0"
    assert bundle.prompt_version == PROMPT_VERSION
    assert "untrusted" in bundle.system.lower()
    assert "{question}" in bundle.user
    assert "{error}" in bundle.repair
    assert "summary" in bundle.response_schema["required"]


def test_missing_prompt_version() -> None:
    with pytest.raises(PromptResourceError, match="unknown prompt version"):
        load_prompt_bundle(DEFAULT_PROMPT_NAME, "9.9.9")
    with pytest.raises(PromptResourceError, match="unknown prompt"):
        load_prompt_bundle("missing-prompt", "1.0.0")


def test_missing_and_unknown_variables() -> None:
    with pytest.raises(PromptResourceError, match="missing required variables"):
        render_template(
            "Hello {name}",
            {},
            required=("name",),
            label="test",
        )
    with pytest.raises(PromptResourceError, match="unknown variables"):
        render_template(
            "Hello {name}",
            {"name": "a", "extra": "b"},
            required=("name",),
            label="test",
        )


def test_stable_rendering() -> None:
    hit = _hit()
    kwargs = {
        "question": "Who handles owners?",
        "style": AnswerStyle.CONCISE,
        "hits": (hit,),
        "citation_labels": ("SRC-1",),
    }
    first = build_user_prompt(**kwargs)
    second = build_user_prompt(**kwargs)
    assert first == second
    assert "OwnersController" in first
    assert "rec-1" in first
    repair_a = build_repair_prompt(error="bad json", citation_labels=("SRC-1",))
    repair_b = build_repair_prompt(error="bad json", citation_labels=("SRC-1",))
    assert repair_a == repair_b
    assert "bad json" in repair_a


def test_repair_prompt_loading() -> None:
    bundle = load_prompt_bundle()
    assert "structured output" in bundle.repair.lower()
    rendered = build_repair_prompt(error="schema failed", citation_labels=("SRC-1",))
    assert "schema failed" in rendered
    assert "SRC-1" in rendered


def test_package_installed_resource_loading() -> None:
    root = prompt_resource_root()
    version = prompt_version_path(DEFAULT_PROMPT_NAME, DEFAULT_PROMPT_VERSION)
    assert root.is_dir()
    assert version.joinpath("system.md").is_file()
    assert version.joinpath("user.md").is_file()
    assert version.joinpath("repair.md").is_file()
    assert version.joinpath("metadata.json").is_file()
    assert version.joinpath("response_schema.json").is_file()
    # importlib.resources path used by installed wheels
    packaged = files(
        "aimf.application.knowledge.answering.prompts"
    ).joinpath(DEFAULT_PROMPT_NAME, DEFAULT_PROMPT_VERSION, "metadata.json")
    metadata = json.loads(packaged.read_text(encoding="utf-8"))
    assert metadata["name"] == DEFAULT_PROMPT_NAME
    assert metadata["version"] == DEFAULT_PROMPT_VERSION


def test_bedrock_and_openai_share_prompt_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    hit = _hit()
    payload = json.dumps(
        {
            "summary": "OwnersController handles owners.",
            "statements": [
                {
                    "text": "OwnersController handles owners.",
                    "citation_labels": ["SRC-1"],
                    "statement_type": "fact",
                    "confidence": "high",
                }
            ],
            "citations": [{"citation_label": "SRC-1"}],
            "evidence_ids": ["rec-1"],
            "limitations": [],
            "confidence": "high",
            "insufficient_evidence": False,
        }
    )
    bedrock_client = MagicMock()
    bedrock_client.converse.return_value = {
        "output": {"message": {"content": [{"text": payload}]}},
        "usage": {"totalTokens": 5},
        "ResponseMetadata": {"RequestId": "b-1"},
    }
    openai_client = MagicMock()
    openai_client.chat.completions.create.return_value = type(
        "R",
        (),
        {
            "choices": [type("C", (), {"message": type("M", (), {"content": payload})()})()],
            "usage": type("U", (), {"total_tokens": 5})(),
            "id": "o-1",
        },
    )()

    request = AnswerProviderRequest(
        question="Who handles owners?",
        normalized_question="who handles owners?",
        style=AnswerStyle.CONCISE,
        hits=(hit,),
        citation_labels=("SRC-1",),
    )
    bedrock = BedrockAnswerProvider(client=bedrock_client)
    openai = OpenAIAnswerProvider(client=openai_client)
    assert bedrock.capabilities().extra["prompt_version"] == PROMPT_VERSION
    assert openai.capabilities().extra["prompt_version"] == PROMPT_VERSION
    assert bedrock.capabilities().extra["prompt_version"] == (
        openai.capabilities().extra["prompt_version"]
    )

    b_result = bedrock.generate(request)
    o_result = openai.generate(request)
    assert any(
        PROMPT_VERSION in d.message for d in b_result.diagnostics if d.code == "provider_usage"
    )
    assert any(
        PROMPT_VERSION in d.message for d in o_result.diagnostics if d.code == "provider_usage"
    )

    system_sent_bedrock = bedrock_client.converse.call_args.kwargs["system"][0]["text"]
    system_sent_openai = openai_client.chat.completions.create.call_args.kwargs[
        "messages"
    ][0]["content"]
    assert system_sent_bedrock == get_system_prompt()
    assert system_sent_openai == get_system_prompt()
    assert system_sent_bedrock == system_sent_openai
