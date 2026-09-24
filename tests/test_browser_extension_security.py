import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_browser_extension_permissions_stay_bounded():
    manifest = json.loads((ROOT / "browser-extension" / "manifest.json").read_text())
    permissions = set(manifest["permissions"])

    assert {"storage", "sidePanel", "tabs", "scripting", "alarms"} <= permissions
    assert "cookies" not in permissions
    assert "webRequest" not in permissions
    assert "nativeMessaging" not in permissions
    assert manifest["host_permissions"] == [
        "http://127.0.0.1/*",
        "http://localhost/*",
    ]
    assert set(manifest["optional_host_permissions"]) == {
        "https://*/*",
        "http://*/*",
    }


def test_browser_executor_does_not_expose_cookie_or_password_apis():
    worker = (ROOT / "browser-extension" / "service-worker.js").read_text()
    server = (ROOT / "src" / "daube_bridge" / "browser_server.py").read_text()

    assert "chrome.cookies" not in worker
    assert "password" not in worker.lower()
    assert "document.cookie" not in worker
    assert "browser_pairing_unauthorized" in server
    assert "x-daube-browser-token" in server
