"""Exercise research through the real worker, HTTP MCP SDK and model prompt."""

from __future__ import annotations

import asyncio
import json
import sys
from uuid import UUID

import httpx
import pytest

from shadow_adapter.adapter import ShadowModeAdapter, Task
from shadow_adapter.api.app import create_app
from shadow_adapter.research import MAX_CONTEXT_CHARS, MCP_URL, USER_AGENT
from shadow_adapter.worker import ShadowWorker

pytestmark = pytest.mark.asyncio


def task(objective="Check Python release information"):
    return {
        "id": "research-task",
        "title": "Private corporate assignment",
        "brief_md": "PRIVATE: internal business plan",
        "opc_metadata": {
            "web_research": {
                "objective": objective,
                "search_queries": ["Python latest stable release"],
                "urls": ["https://www.python.org/downloads/"],
            }
        },
    }


@pytest.fixture
def wire(monkeypatch):
    """Intercept HTTP sends, retaining the SDK's real request construction."""
    for key in ("LOCAL_OPENAI_API_KEY", "LOCAL_ANTHROPIC_KEY", "OLLAMA_HOST", "SHADOW_SEARCH_PROVIDER"):
        monkeypatch.delenv(key, raising=False)
    original_send = httpx.AsyncClient.send
    state = {"mcp": [], "models": [], "failure": None, "entered": asyncio.Event(), "source_size": 0}

    async def send(client, request, **kwargs):
        if str(request.url) == MCP_URL:
            payload = json.loads(request.content)
            state["mcp"].append((request, payload))
            method = payload["method"]
            if method == "notifications/initialized":
                return httpx.Response(202, request=request)
            if method == "initialize":
                result = {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "scripted-parallel", "version": "1"},
                }
            elif method == "tools/list":
                result = {
                    "tools": [{"name": name, "inputSchema": {"type": "object"}} for name in ("web_search", "web_fetch")]
                }
            else:
                assert method == "tools/call"
                state["entered"].set()
                if state["failure"] == "wait":
                    await asyncio.Event().wait()
                if state["failure"] == "http":
                    return httpx.Response(503, request=request)
                if state["failure"] == "quota":
                    return httpx.Response(429, headers={"Retry-After": "60"}, request=request)
                # Yield to allow concurrent research tasks to interleave.
                await asyncio.sleep(0)
                source = {
                    "url": "https://www.python.org/downloads/",
                    "excerpts": ["Python release evidence" + "x" * state["source_size"]],
                }
                result = {
                    "isError": state["failure"] == "tool",
                    "content": [{"type": "text", "text": json.dumps({"results": [source]})}],
                }
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": payload["id"], "result": result}, request=request)
        if request.url.host == "model.test":
            payload = json.loads(request.content)
            state["models"].append((request, payload))
            prompt = payload.get("prompt") or payload["messages"][0]["content"]
            text = (
                "Grounded deliverable: https://www.python.org/downloads/"
                if "Python release evidence" in prompt
                else "No research"
            )
            return httpx.Response(
                200,
                json={"response": text, "choices": [{"message": {"content": text}}], "content": [{"text": text}]},
                request=request,
            )
        return await original_send(client, request, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    return state


@pytest.mark.parametrize("provider", ["ollama", "openai", "anthropic", "vllm", "litellm"])
async def test_claim_research_model_and_submit(provider, wire, shadow_config, shadow_store, security):
    """Scripted model sees source context; the normal caller submits its output."""
    app = create_app(shadow_config)
    app.state.config, app.state.shadow_store, app.state.security = shadow_config, shadow_store, security
    adapter = ShadowModeAdapter(shadow_config=shadow_config, shadow_store=shadow_store)
    incoming = task()
    await adapter.execute(
        Task(
            id="research-" + provider,
            title=incoming["title"],
            description=incoming["brief_md"],
            metadata=incoming["opc_metadata"],
        )
    )
    worker = ShadowWorker(
        server_url="http://testserver",
        username="researcher",
        password="password123",
        provider=provider,
        model="configured-model:exact",
        api_base="https://model.test/v1",
        api_key="model-secret",
    )
    assert worker.search_provider == "parallel"
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        assert await worker.process_one_task(client)
    parked = await shadow_store.get_task_by_opc_id("research-" + provider)
    assert parked.deliverable_text == "Grounded deliverable: https://www.python.org/downloads/"
    calls = [body["params"] for _, body in wire["mcp"] if body["method"] == "tools/call"]
    assert [call["name"] for call in calls] == ["web_search", "web_fetch"]
    assert len({call["arguments"]["session_id"] for call in calls}) == 1
    assert UUID(calls[0]["arguments"]["session_id"]).version == 4
    assert all(call["arguments"]["model_name"] == "configured-model:exact" for call in calls)
    for request, body in wire["mcp"]:
        assert str(request.url) == MCP_URL
        assert request.headers["User-Agent"] == USER_AGENT
        assert "authorization" not in request.headers and "x-api-key" not in request.headers
        assert "PRIVATE" not in json.dumps(body) and incoming["title"] not in json.dumps(body)
    model_request, model_payload = wire["models"][0]
    assert "PRIVATE" in json.dumps(model_payload)
    assert "untrusted source material" in json.dumps(model_payload)
    if provider in ("openai", "vllm", "litellm"):
        assert model_request.headers["Authorization"] == "Bearer model-secret"
    if provider == "anthropic":
        assert model_request.headers["x-api-key"] == "model-secret"


async def test_permissions_saved_disable_and_explicit_override(wire, monkeypatch):
    monkeypatch.setenv("SHADOW_SEARCH_PROVIDER", "none")
    async with httpx.AsyncClient() as client:
        disabled = ShadowWorker(provider="openai", api_base="https://model.test")
        assert await disabled.execute_local_model(client, task()) == "No research"
        assert not wire["mcp"]
        enabled = ShadowWorker(provider="openai", api_base="https://model.test", search_provider="parallel")
        no_permission = task()
        no_permission.pop("opc_metadata")
        assert await enabled.execute_local_model(client, no_permission) == "No research"
        assert not wire["mcp"]
        assert "Grounded" in await enabled.execute_local_model(client, task())
    with pytest.raises(ValueError, match="search_provider"):
        ShadowWorker(search_provider="unknown")


async def test_custom_and_mock_handlers_are_preserved(wire):
    async def custom(received):
        assert received["title"] == "Private corporate assignment"
        return "custom-owned result"

    async with httpx.AsyncClient() as client:
        worker = ShadowWorker(custom_handler=custom)
        assert await worker.execute_local_model(client, task()) == "custom-owned result"
        mock = ShadowWorker(provider="mock")
        assert "DECENTRALIZED SILICON DELIVERABLE" in await mock.execute_local_model(client, task())
    assert not wire["mcp"] and not wire["models"]


@pytest.mark.parametrize("field,tool", [("urls", "web_fetch"), ("search_queries", "web_search")])
async def test_search_or_fetch_can_be_requested_independently(wire, field, tool):
    incoming = task()
    request = incoming["opc_metadata"]["web_research"]
    request.pop("search_queries" if field == "urls" else "urls")
    async with httpx.AsyncClient() as client:
        result = await ShadowWorker(provider="openai", api_base="https://model.test").execute_local_model(
            client, incoming
        )
    assert "Grounded" in result
    assert [body["params"]["name"] for _, body in wire["mcp"] if body["method"] == "tools/call"] == [tool]


@pytest.mark.parametrize(
    "research",
    [
        {},
        {"objective": "Need evidence"},
        {"objective": "Need evidence", "urls": ["file:///etc/passwd"]},
        {"objective": "Need evidence", "urls": ["https://user:secret@example.com/"]},
        {"objective": "Need evidence", "search_queries": [""]},
    ],
)
async def test_invalid_research_never_leaves_worker(wire, research):
    incoming = task()
    incoming["opc_metadata"]["web_research"] = research
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError):
            await ShadowWorker(provider="openai").execute_local_model(client, incoming)
    assert not wire["mcp"] and not wire["models"]


@pytest.mark.parametrize("failure", ["http", "quota", "tool"])
async def test_research_errors_do_not_produce_deliverables(wire, failure):
    wire["failure"] = failure
    async with httpx.AsyncClient() as client:
        with pytest.raises(Exception):
            await ShadowWorker(provider="openai").execute_local_model(client, task())
    calls = [body for _, body in wire["mcp"] if body["method"] == "tools/call"]
    assert len(calls) == 1  # No hidden retry or rotated research ID after a quota.
    assert not wire["models"]


async def test_timeout_and_cancellation_propagate(wire):
    wire["failure"] = "wait"
    async with httpx.AsyncClient() as client:
        with pytest.raises(TimeoutError):
            await ShadowWorker(provider="openai", research_timeout=0.1).execute_local_model(client, task())
        wire["entered"].clear()
        pending = asyncio.create_task(ShadowWorker(provider="openai").execute_local_model(client, task()))
        await asyncio.wait_for(wire["entered"].wait(), timeout=2)
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
    assert not wire["models"]


async def test_one_worker_isolates_concurrent_and_new_research_runs(wire):
    worker = ShadowWorker(provider="openai", api_base="https://model.test")
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(worker.execute_local_model(client, task(f"Research run {i}")) for i in range(2)))
        await worker.execute_local_model(client, task("Research run 0"))  # Explicit rerun is a fresh research run.
    grouped = {}
    for _, body in wire["mcp"]:
        if body["method"] == "tools/call":
            args = body["params"]["arguments"]
            grouped.setdefault(args["session_id"], []).append((args["objective"], body["params"]["name"]))
    assert len(grouped) == 3
    assert all(len(calls) == 2 and calls[0][0] == calls[1][0] for calls in grouped.values())
    assert all([name for _, name in calls] == ["web_search", "web_fetch"] for calls in grouped.values())


async def test_context_is_bounded(wire):
    wire["source_size"] = MAX_CONTEXT_CHARS
    async with httpx.AsyncClient() as client:
        await ShadowWorker(provider="ollama", api_base="https://model.test").execute_local_model(client, task())
    prompt = wire["models"][0][1]["prompt"]
    assert "[Web context truncated]" in prompt
    assert len(prompt) < MAX_CONTEXT_CHARS + 1000


async def test_cli_disable_reaches_worker(monkeypatch, wire):
    from shadow_adapter.worker import main

    observed = []

    async def login(self, client):
        observed.append(self.search_provider)

    async def process(self, client):
        return False

    monkeypatch.setattr(sys, "argv", ["shadow-worker", "--once", "--search-provider", "none"])
    monkeypatch.setattr(ShadowWorker, "login", login)
    monkeypatch.setattr(ShadowWorker, "process_one_task", process)
    await asyncio.to_thread(main)
    assert observed == ["none"]
    assert not wire["mcp"]
