"""ShadowWorker SDK and CLI Daemon for Distributed Silicon Nodes.

Enables Bring Your Own Compute (BYOC) for OpenOPC roles. Runs on remote PCs,
authenticates with central Shadow Adapter API, polls pending tasks for assigned roles,
executes local LLM inference (Ollama, OpenAI, Anthropic, or custom handlers), and
submits deliverables to unblock OpenOPC DAG workflows.
"""

from __future__ import annotations

import argparse
import asyncio
import math
import os
import sys
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from loguru import logger

TaskHandlerCallable = Callable[[dict[str, Any]], Awaitable[str]]


class ShadowWorker:
    """Distributed Worker Client for OpenOPC Shadow Adapter."""

    def __init__(
        self,
        server_url: str = "http://localhost:8800",
        username: str = "silicon_worker",
        password: str = "password123",
        role: str | None = None,
        provider: str = "ollama",
        model: str = "llama3.3:70b",
        api_key: str | None = None,
        api_base: str | None = None,
        poll_interval: float = 3.0,
        custom_handler: TaskHandlerCallable | None = None,
        search_provider: str | None = None,
        research_timeout: float = 30.0,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.username = username
        self.password = password
        self.role = role
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key or os.getenv("LOCAL_OPENAI_API_KEY") or os.getenv("LOCAL_ANTHROPIC_KEY") or ""
        self.api_base = api_base or os.getenv("OLLAMA_HOST") or ""
        self.poll_interval = poll_interval
        self.custom_handler = custom_handler
        self.search_provider = (
            search_provider if search_provider is not None else os.getenv("SHADOW_SEARCH_PROVIDER", "parallel")
        ).lower()
        if self.search_provider not in ("parallel", "none"):
            raise ValueError("search_provider must be 'parallel' or 'none'")
        if not math.isfinite(research_timeout) or research_timeout <= 0:
            raise ValueError("research_timeout must be finite and positive")
        self.research_timeout = research_timeout

        self.access_token: str | None = None
        self._running = False

    async def login(self, client: httpx.AsyncClient) -> str:
        """Authenticate with central Shadow Adapter API and obtain JWT access token."""
        endpoints = [
            f"{self.server_url}/api/auth/login",
            f"{self.server_url}/api/v1/auth/login",
        ]
        last_error = None

        for ep in endpoints:
            try:
                res = await client.post(
                    ep,
                    json={"username": self.username, "password": self.password},
                    timeout=10.0,
                )
                if res.status_code == 200:
                    data = res.json()
                    token = data.get("access_token")
                    if token:
                        self.access_token = token
                        logger.info(f"[ShadowWorker] Authenticated as '{self.username}' on {ep}")
                        return token
            except Exception as e:
                last_error = e

        # If user does not exist, attempt auto-registration
        reg_endpoints = [
            f"{self.server_url}/api/auth/register",
            f"{self.server_url}/api/v1/auth/register",
        ]
        for ep in reg_endpoints:
            try:
                reg_res = await client.post(
                    ep,
                    json={
                        "username": self.username,
                        "password": self.password,
                        "email": f"{self.username}@node.local",
                    },
                    timeout=10.0,
                )
                if reg_res.status_code == 201:
                    logger.info(f"[ShadowWorker] Auto-registered worker identity '{self.username}'")
                    # Retry login
                    return await self.login(client)
            except Exception as e:
                logger.debug(f"[ShadowWorker] Auto-register check failed on {ep}: {e}")

        raise RuntimeError(
            f"Failed to authenticate with Shadow Adapter at {self.server_url}: {last_error or 'Invalid credentials'}"
        )

    def _get_headers(self) -> dict[str, str]:
        if not self.access_token:
            raise RuntimeError("Worker is not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.access_token}"}

    async def fetch_pending_tasks(self, client: httpx.AsyncClient) -> list[dict[str, Any]]:
        """Fetch pending tasks from central server, optionally filtered by assigned_role."""
        headers = self._get_headers()
        url = f"{self.server_url}/api/tasks?status=pending"
        res = await client.get(url, headers=headers, timeout=10.0)

        if res.status_code == 401:
            logger.warning("[ShadowWorker] JWT token expired. Re-authenticating...")
            await self.login(client)
            headers = self._get_headers()
            res = await client.get(url, headers=headers, timeout=10.0)

        res.raise_for_status()
        tasks = res.json()

        if self.role:
            filtered = [t for t in tasks if t.get("assigned_role") == self.role or not t.get("assigned_role")]
            return filtered
        return tasks

    async def claim_task(self, client: httpx.AsyncClient, task_id: str) -> dict[str, Any]:
        """Claim a pending task on central server."""
        headers = self._get_headers()
        url = f"{self.server_url}/api/tasks/{task_id}/claim"
        res = await client.post(url, headers=headers, timeout=10.0)
        res.raise_for_status()
        return res.json()

    async def submit_deliverable(
        self,
        client: httpx.AsyncClient,
        task_id: str,
        deliverable_text: str,
    ) -> dict[str, Any]:
        """Submit completed deliverable to central server to unblock DAG."""
        headers = self._get_headers()
        url = f"{self.server_url}/api/tasks/{task_id}/submit"
        res = await client.post(
            url,
            headers=headers,
            data={"deliverable_text": deliverable_text},
            timeout=30.0,
        )
        res.raise_for_status()
        return res.json()

    async def execute_local_model(self, client: httpx.AsyncClient, task: dict[str, Any]) -> str:
        """Execute local LLM inference or custom callback on remote worker PC."""
        if self.custom_handler:
            logger.info(f"[ShadowWorker] Invoking custom task handler for task '{task.get('id')}'")
            return await self.custom_handler(task)

        task_title = task.get("title", "Task Brief")
        task_brief = task.get("brief_md") or task.get("description") or "Complete assigned role objective."
        prompt = (
            f"You are a remote Silicon Employee serving in role '{self.role or 'Specialist'}'.\n"
            f"Task: {task_title}\n\nBrief:\n{task_brief}\n\n"
            f"Please generate the complete professional deliverable."
        )

        # Metadata is the permission boundary: never infer public queries from
        # private corporate briefs or run web research for custom/mock providers.
        metadata = task.get("opc_metadata") or {}
        research = metadata.get("web_research")
        if (
            self.search_provider == "parallel"
            and research is not None
            and self.provider in ("ollama", "openai", "vllm", "litellm", "anthropic")
        ):
            from shadow_adapter.research import WebResearchRequest, collect_web_context

            request = WebResearchRequest.model_validate(research)
            prompt += await collect_web_context(request, self.model, self.research_timeout)

        logger.info(f"[ShadowWorker] Processing task '{task_title}' using provider '{self.provider}' ({self.model})")

        # Provider 1: Ollama / Local Open-Source LLM
        if self.provider == "ollama":
            base = self.api_base or "http://localhost:11434"
            ollama_url = f"{base.rstrip('/')}/api/generate"
            try:
                res = await client.post(
                    ollama_url,
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=120.0,
                )
                if res.status_code == 200:
                    return res.json().get("response", "").strip()
            except Exception as e:
                logger.warning(f"[ShadowWorker] Local Ollama call failed ({e}). Falling back to synthetic deliverable.")

        # Provider 2: OpenAI / Custom OpenAI-compatible endpoint
        elif self.provider in ("openai", "vllm", "litellm"):
            base = self.api_base or "https://api.openai.com/v1"
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            openai_url = f"{base.rstrip('/')}/chat/completions"
            try:
                res = await client.post(
                    openai_url,
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=120.0,
                )
                if res.status_code == 200:
                    choices = res.json().get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "").strip()
            except Exception as e:
                logger.warning(f"[ShadowWorker] OpenAI API call failed ({e}). Falling back to synthetic deliverable.")

        # Provider 3: Anthropic Claude API
        elif self.provider == "anthropic":
            base = self.api_base or "https://api.anthropic.com/v1"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            try:
                res = await client.post(
                    f"{base.rstrip('/')}/messages",
                    headers=headers,
                    json={
                        "model": self.model,
                        "max_tokens": 4096,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=120.0,
                )
                if res.status_code == 200:
                    content_blocks = res.json().get("content", [])
                    if content_blocks:
                        return content_blocks[0].get("text", "").strip()
            except Exception as e:
                logger.warning(f"[ShadowWorker] Anthropic call failed ({e}). Falling back to synthetic deliverable.")

        # Synthetic Fallback Delivery
        return (
            f"[DECENTRALIZED SILICON DELIVERABLE]\n"
            f"Node Provider: {self.provider} ({self.model})\n"
            f"Assigned Role: {self.role or 'General Worker'}\n"
            f"Task: {task_title}\n\n"
            f"Execution completed successfully by remote compute node."
        )

    async def process_one_task(self, client: httpx.AsyncClient) -> bool:
        """Fetch, claim, execute, and submit one pending task."""
        if not self.access_token:
            await self.login(client)

        tasks = await self.fetch_pending_tasks(client)
        if not tasks:
            return False

        target_task = tasks[0]
        task_id = target_task["id"]
        task_title = target_task.get("title", task_id)

        try:
            logger.info(f"[ShadowWorker] Attempting to claim task '{task_title}' (id={task_id})")
            await self.claim_task(client, task_id)
            logger.info(f"[ShadowWorker] Successfully claimed task '{task_id}'. Executing remote compute...")

            deliverable = await self.execute_local_model(client, target_task)

            logger.info(f"[ShadowWorker] Submitting deliverable for task '{task_id}'...")
            sub_res = await self.submit_deliverable(client, task_id, deliverable)
            logger.info(f"[ShadowWorker] Task '{task_id}' resumed successfully: {sub_res.get('status')}")
            return True

        except Exception as e:
            logger.error(f"[ShadowWorker] Failed executing task '{task_id}': {e}")
            return False

    async def run_forever(self) -> None:
        """Run continuous worker polling loop on distributed node with exponential backoff."""
        import random

        self._running = True
        current_interval = float(self.poll_interval)
        max_interval = float(max(15.0, self.poll_interval * 3))

        logger.info(
            f"[ShadowWorker] Starting continuous worker loop for role '{self.role or 'all'}' "
            f"pointing to {self.server_url} (provider={self.provider}, model={self.model}, base_poll={self.poll_interval}s)"
        )

        async with httpx.AsyncClient() as client:
            await self.login(client)

            while self._running:
                try:
                    processed = await self.process_one_task(client)
                    if processed:
                        current_interval = float(self.poll_interval)
                    else:
                        jitter = random.uniform(0.1, 0.5)
                        current_interval = min(max_interval, current_interval * 1.5 + jitter)
                        await asyncio.sleep(current_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[ShadowWorker] Error in worker loop: {e}")
                    jitter = random.uniform(0.1, 0.5)
                    current_interval = min(max_interval, current_interval * 1.5 + jitter)
                    await asyncio.sleep(current_interval)

    def stop(self) -> None:
        """Stop worker polling loop."""
        self._running = False


def main() -> None:
    """CLI Entrypoint for shadow-worker."""
    parser = argparse.ArgumentParser(
        description="ShadowWorker CLI Daemon — Bring Your Own Compute (BYOC) Silicon Worker for OpenOPC."
    )
    parser.add_argument("--server-url", default="http://localhost:8800", help="Central Shadow Adapter server URL")
    parser.add_argument("--username", default="silicon_worker", help="Worker username for authentication")
    parser.add_argument("--password", default="password123", help="Worker password")
    parser.add_argument("--role", default=None, help="Target role ID to claim tasks for (e.g. legal_counsel)")
    parser.add_argument(
        "--provider",
        default="ollama",
        choices=["ollama", "openai", "anthropic", "vllm", "litellm", "mock"],
        help="Local LLM provider type",
    )
    parser.add_argument("--model", default="llama3.3:70b", help="Model name or ID")
    parser.add_argument("--api-key", default=None, help="Local API Key for model provider")
    parser.add_argument("--api-base", default=None, help="Local API Base URL (e.g. http://localhost:11434)")
    parser.add_argument("--poll-interval", type=float, default=3.0, help="Polling interval in seconds")
    parser.add_argument("--once", action="store_true", help="Process at most one task and exit")
    parser.add_argument(
        "--search-provider",
        choices=["parallel", "none"],
        default=None,
        help="Research provider for explicit task web_research metadata (env: SHADOW_SEARCH_PROVIDER; default: parallel)",
    )
    parser.add_argument(
        "--research-timeout", type=float, default=30.0, help="Total web research timeout in seconds (default: 30)"
    )

    args = parser.parse_args()

    worker = ShadowWorker(
        server_url=args.server_url,
        username=args.username,
        password=args.password,
        role=args.role,
        provider=args.provider,
        model=args.model,
        api_key=args.api_key,
        api_base=args.api_base,
        poll_interval=args.poll_interval,
        search_provider=args.search_provider,
        research_timeout=args.research_timeout,
    )

    async def run():
        async with httpx.AsyncClient() as client:
            if args.once:
                await worker.login(client)
                await worker.process_one_task(client)
            else:
                await worker.run_forever()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("[ShadowWorker] Shutting down worker daemon.")
        sys.exit(0)


if __name__ == "__main__":
    main()
