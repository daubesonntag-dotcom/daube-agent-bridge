#!/bin/sh
# D'AUBE Ti Messenger: per-user installation of pre-reviewed MCP source.
# No sudo, daemon, scheduler, token creation, secret copying or public ingress.
set -eu
repo='https://github.com/daubesonntag-dotcom/daube-agent-bridge.git'
branch='feature/ti-messenger-mcp-20261107'
root="${HOME}/.local/share/daube-ti-messenger"
if ! command -v python3 >/dev/null 2>&1;then echo HOLD_PYTHON3_REQUIRED >&2;exit 2;fi
if ! command -v git >/dev/null 2>&1;then echo HOLD_GIT_REQUIRED >&2;exit 2;fi
if [ -e "$root" ];then echo "HOLD_EXISTING_INSTALL: $root" >&2;exit 3;fi
mkdir -p "${HOME}/.local/share"
git clone --depth 1 --branch "$branch" "$repo" "$root"
cd "$root/integrations/ti-messenger"
src_sha=$(git hash-object ti_messenger_mcp.py)
test_sha=$(git hash-object tests/test_ti_messenger.py)
if [ "$src_sha" != '9d36954d7b356f971a244c9cb15c998fe4b023f0' ] || [ "$test_sha" != '9889574aa990a8d723897dde17af48a0ead59f14' ];then
 echo 'HOLD_PINNED_CODE_CHANGED_DO_NOT_REGISTER' >&2;exit 4
fi
python3 -m py_compile ti_messenger_mcp.py tests/test_ti_messenger.py
python3 -m unittest discover -s tests -v
echo "SOURCE_VALIDATED"
mcp_file="$root/integrations/ti-messenger/ti_messenger_mcp.py"
if command -v codex >/dev/null 2>&1;then
 if codex mcp get daube-ti-messenger >/dev/null 2>&1;then
  echo "HOLD_EXISTING_CODEX_MCP_ENTRY_INSPECT_BEFORE_REPLACEMENT"
 else
  if codex mcp add daube-ti-messenger -- python3 "$mcp_file";then
   if codex mcp get daube-ti-messenger >/dev/null 2>&1;then
    echo "CODEX_MCP_REGISTERED"
   else
    echo 'HOLD_CODEX_REGISTRATION_READBACK_MISSING' >&2;exit 5
   fi
  else
   echo 'HOLD_CODEX_MCP_REGISTER_FAILED' >&2;exit 5
  fi
 fi
else
 echo 'HOLD_NO_CODEX_CLI_USE_HOSTED_MCP_OR_OTHER_SUPPORTED_CLIENT'
fi
echo "MCP_ENTRY: python3 $mcp_file"
echo 'Before sending, the Ti cloud secret store must provide the ALREADY AUTHORIZED service identity as DAUBE_TI_CF_ACCESS_CLIENT_ID / DAUBE_TI_CF_ACCESS_CLIENT_SECRET; never paste it in chat/Git.'
echo 'Do not claim LIVE until daube_messenger_audit reads authorized APIs and a separate recipient sends a durable ACK.'
