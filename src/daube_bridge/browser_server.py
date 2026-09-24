from __future__ import annotations

import hmac
import os
from typing import Any

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response

from .browser_broker import BrowserBroker

broker = BrowserBroker()

mcp = FastMCP(
    "D'AUBE Browser Bridge",
    instructions=(
        "Operate only an explicitly paired local browser session. Discover current "
        "capabilities before writes and require post-action verification receipts."
    ),
)

READ_BROWSER = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

WRITE_BROWSER = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=True,
)


def _pairing_token() -> str:
    return os.getenv("DAUBE_BROWSER_PAIRING_TOKEN", "").strip()


def _authorized(request: Request) -> bool:
    expected = _pairing_token()
    supplied = request.headers.get("x-daube-browser-token", "")
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


def _require_token(request: Request) -> Response | None:
    if not _pairing_token():
        return JSONResponse({"error": "pairing_token_not_configured"}, status_code=503)
    if not _authorized(request):
        return JSONResponse({"error": "browser_pairing_unauthorized"}, status_code=401)
    return None


@mcp.tool(title="Browser bridge status", annotations=READ_BROWSER)
def browser_status() -> dict[str, Any]:
    """Return current paired-browser health and observed capabilities."""
    return broker.status()


@mcp.tool(title="List browser tabs", annotations=READ_BROWSER)
async def browser_tabs() -> dict[str, Any]:
    """List tabs from the currently paired browser session."""
    return await broker.submit("tabs.read")


@mcp.tool(title="Read browser page", annotations=READ_BROWSER)
async def browser_read_page(tab_id: int | None = None) -> dict[str, Any]:
    """Read bounded visible page text and interactive-element metadata without reading cookies."""
    return await broker.submit("page.read", {"tabId": tab_id})


@mcp.tool(title="Capture browser screenshot", annotations=READ_BROWSER)
async def browser_screenshot(tab_id: int | None = None) -> dict[str, Any]:
    """Capture the visible browser tab through the paired extension."""
    return await broker.submit("screenshot", {"tabId": tab_id})


@mcp.tool(title="Navigate browser tab", annotations=WRITE_BROWSER)
async def browser_navigate(url: str, tab_id: int | None = None) -> dict[str, Any]:
    """Navigate an existing or active tab and verify the resulting URL."""
    return await broker.submit("navigate", {"url": url, "tabId": tab_id})


@mcp.tool(title="Click browser element", annotations=WRITE_BROWSER)
async def browser_click(
    selector: str | None = None,
    text: str | None = None,
    tab_id: int | None = None,
) -> dict[str, Any]:
    """Click one element selected by CSS selector or visible text, then read back page state."""
    if not selector and not text:
        raise ValueError("browser_click_requires_selector_or_text")
    return await broker.submit(
        "click",
        {"selector": selector, "text": text, "tabId": tab_id},
    )


@mcp.tool(title="Type into browser field", annotations=WRITE_BROWSER)
async def browser_type(
    value: str,
    selector: str | None = None,
    text: str | None = None,
    tab_id: int | None = None,
) -> dict[str, Any]:
    """Type into one field selected by CSS selector or accessible text and verify length only."""
    if not selector and not text:
        raise ValueError("browser_type_requires_selector_or_text")
    return await broker.submit(
        "type",
        {"selector": selector, "text": text, "value": value, "tabId": tab_id},
    )


@mcp.custom_route("/browser/v1/health", methods=["GET"])
async def browser_health(request: Request) -> JSONResponse:
    return JSONResponse(broker.status())


@mcp.custom_route("/browser/v1/hello", methods=["POST"])
async def browser_hello(request: Request) -> Response:
    denied = _require_token(request)
    if denied:
        return denied
    payload = await request.json()
    capabilities = payload.get("capabilities", [])
    if not isinstance(capabilities, list):
        return JSONResponse({"error": "capabilities_must_be_list"}, status_code=400)
    result = broker.hello(payload.get("connectorId", "browser-extension"), capabilities)
    return JSONResponse(result)


@mcp.custom_route("/browser/v1/jobs/next", methods=["POST"])
async def browser_next_job(request: Request) -> Response:
    denied = _require_token(request)
    if denied:
        return denied
    payload = await request.json()
    capabilities = payload.get("capabilities", [])
    if isinstance(capabilities, list):
        broker.hello(payload.get("connectorId", "browser-extension"), capabilities)
    job = await broker.next_job(timeout_seconds=25.0)
    if job is None:
        return Response(status_code=204)
    return JSONResponse(job)


@mcp.custom_route("/browser/v1/jobs/{job_id}/receipt", methods=["POST"])
async def browser_receipt(request: Request) -> Response:
    denied = _require_token(request)
    if denied:
        return denied
    job_id = request.path_params["job_id"]
    payload = await request.json()
    if payload.get("jobId") != job_id:
        return JSONResponse({"error": "receipt_job_mismatch"}, status_code=400)
    accepted = broker.complete(job_id, payload)
    return JSONResponse({"accepted": accepted}, status_code=200 if accepted else 409)


def main() -> None:
    host = os.getenv("DAUBE_BROWSER_HOST", "127.0.0.1")
    port = int(os.getenv("DAUBE_BROWSER_PORT", "8000"))
    mcp.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    main()
