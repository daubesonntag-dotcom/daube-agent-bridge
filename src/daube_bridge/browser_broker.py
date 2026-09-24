from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


ACTION_CAPABILITIES = {
    "tabs.read": "tabs.read",
    "page.read": "page.read",
    "navigate": "navigate",
    "click": "click",
    "type": "type",
    "screenshot": "screenshot",
}


@dataclass(slots=True)
class BrowserSession:
    connector_id: str
    capabilities: set[str]
    observed_at: str
    monotonic_at: float


class BrowserBroker:
    def __init__(self, *, session_ttl_seconds: float = 45.0) -> None:
        self.session_ttl_seconds = session_ttl_seconds
        self._queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._session: BrowserSession | None = None

    def hello(self, connector_id: str, capabilities: list[str]) -> dict[str, Any]:
        normalized = {str(item).strip() for item in capabilities if str(item).strip()}
        now = datetime.now(timezone.utc).isoformat()
        self._session = BrowserSession(
            connector_id=str(connector_id or "browser-extension").strip() or "browser-extension",
            capabilities=normalized,
            observed_at=now,
            monotonic_at=time.monotonic(),
        )
        return self.status()

    def status(self) -> dict[str, Any]:
        session = self._session
        healthy = bool(
            session
            and (time.monotonic() - session.monotonic_at) <= self.session_ttl_seconds
        )
        return {
            "schema": "daube.browser-bridge.status.v1",
            "connected": healthy,
            "connectorId": session.connector_id if session else None,
            "capabilities": sorted(session.capabilities) if session else [],
            "lastHeartbeat": session.observed_at if session else None,
            "pendingJobs": len(self._pending),
            "queuedJobs": self._queue.qsize(),
        }

    def _assert_executable(self, action: str) -> None:
        status = self.status()
        if not status["connected"]:
            raise RuntimeError("browser_bridge_not_connected")
        capability = ACTION_CAPABILITIES.get(action)
        if capability is None:
            raise RuntimeError("browser_bridge_action_not_allowed")
        if capability not in status["capabilities"]:
            raise RuntimeError("browser_bridge_capability_not_observed:" + capability)

    async def submit(
        self,
        action: str,
        arguments: dict[str, Any] | None = None,
        *,
        timeout_seconds: float = 45.0,
    ) -> dict[str, Any]:
        self._assert_executable(action)
        job_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[job_id] = future
        job = {
            "schema": "daube.browser-job.v1",
            "id": job_id,
            "action": action,
            "arguments": arguments or {},
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        await self._queue.put(job)
        try:
            receipt = await asyncio.wait_for(future, timeout=timeout_seconds)
        except TimeoutError as exc:
            raise RuntimeError("browser_bridge_receipt_timeout") from exc
        finally:
            self._pending.pop(job_id, None)

        if receipt.get("jobId") != job_id:
            raise RuntimeError("browser_bridge_receipt_job_mismatch")
        if receipt.get("ok") is not True:
            raise RuntimeError(
                "browser_bridge_action_failed:" + str(receipt.get("error") or "unknown")
            )
        if action in {"navigate", "click", "type"} and receipt.get("verified") is not True:
            raise RuntimeError("browser_bridge_write_not_verified")
        return receipt

    async def next_job(self, *, timeout_seconds: float = 25.0) -> dict[str, Any] | None:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout_seconds)
        except TimeoutError:
            return None

    def complete(self, job_id: str, receipt: dict[str, Any]) -> bool:
        future = self._pending.get(job_id)
        if future is None or future.done():
            return False
        future.set_result(receipt)
        return True
