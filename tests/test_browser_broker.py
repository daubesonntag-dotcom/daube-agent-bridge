import asyncio

import pytest

from daube_bridge.browser_broker import BrowserBroker


def test_browser_broker_requires_observed_capability():
    broker = BrowserBroker()
    broker.hello("test-extension", ["page.read"])

    async def run():
        with pytest.raises(RuntimeError, match="capability_not_observed"):
            await broker.submit("click", {"text": "Campaigns"}, timeout_seconds=0.05)

    asyncio.run(run())


def test_browser_broker_write_requires_verified_receipt():
    async def run():
        broker = BrowserBroker()
        broker.hello("test-extension", ["navigate"])

        pending = asyncio.create_task(
            broker.submit("navigate", {"url": "https://example.com"}, timeout_seconds=1)
        )
        job = await broker.next_job(timeout_seconds=0.1)
        assert job is not None

        accepted = broker.complete(
            job["id"],
            {
                "jobId": job["id"],
                "action": "navigate",
                "ok": True,
                "verified": False,
                "result": {"url": "https://example.com"},
            },
        )
        assert accepted is True
        with pytest.raises(RuntimeError, match="write_not_verified"):
            await pending

    asyncio.run(run())


def test_browser_broker_accepts_verified_write_receipt():
    async def run():
        broker = BrowserBroker()
        broker.hello("test-extension", ["navigate"])

        pending = asyncio.create_task(
            broker.submit("navigate", {"url": "https://example.com"}, timeout_seconds=1)
        )
        job = await broker.next_job(timeout_seconds=0.1)
        assert job is not None
        receipt = {
            "jobId": job["id"],
            "action": "navigate",
            "ok": True,
            "verified": True,
            "stateBefore": {"url": "about:blank"},
            "stateAfter": {"url": "https://example.com"},
        }
        assert broker.complete(job["id"], receipt) is True
        result = await pending
        assert result["verified"] is True
        assert result["stateAfter"]["url"] == "https://example.com"

    asyncio.run(run())


def test_browser_broker_session_health_expires():
    broker = BrowserBroker(session_ttl_seconds=0.001)
    broker.hello("test-extension", ["tabs.read"])

    async def run():
        await asyncio.sleep(0.01)
        assert broker.status()["connected"] is False

    asyncio.run(run())
