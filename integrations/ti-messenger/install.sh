#!/bin/sh
set -eu
# Installs only in the calling user's home; no sudo, daemon, token, or cron.
repo="https://github.com/daubesonntag-dotcom/daube-agent-bridge.git"
branch="feature/ti-messenger-mcp-20261107"
root="${HOME}/.local/share/daube-ti-messenger"
if ! command -v python3 >/dev/null 2>&1; then echo "HOLD_PYTHON3_REQUIRED" >&2; exit 2; fi
if ! command -v git >/dev/null 2>&1; then echo "HOLD_GIT_REQUIRED" >&2; exit 2; fi
if [ -e "${root}" ]; then
  echo "HOLD_EXISTING_INSTALL: ${root}; inspect before replacing" >&2; exit 3
fi
mkdir -p "${HOME}/.local/share"
git clone --depth 1 --branch "${branch}" "${repo}" "${root}"
cd "${root}/integrations/ti-messenger"
python3 -m unittest discover -s tests -v
python3 -m py_compile ti_messenger_mcp.py
echo "INSTALLED_SOURCE_VALIDATED"
echo "MCP command: python3 ${root}/integrations/ti-messenger/ti_messenger_mcp.py"
echo "Set DAUBE_TI_CF_ACCESS_CLIENT_ID and DAUBE_TI_CF_ACCESS_CLIENT_SECRET in Ti's existing secret store; configure only preapproved deployed Messenger endpoints."
echo "This is NOT proof that a Cloudflare machine room grant is active."
