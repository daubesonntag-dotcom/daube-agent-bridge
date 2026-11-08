#!/bin/sh
# D'AUBE Ti Messenger: per-user installation of pre-reviewed MCP source.
# No sudo, daemon, scheduler, token creation, secret copying or public ingress.
set -eu
umask 077
repo='https://github.com/daubesonntag-dotcom/daube-agent-bridge.git'
branch='feature/ti-messenger-mcp-20261107'
root="${HOME}/.local/share/daube-ti-messenger"
if ! command -v python3 >/dev/null 2>&1;then echo HOLD_PYTHON3_REQUIRED >&2;exit 2;fi
if ! command -v git >/dev/null 2>&1;then echo HOLD_GIT_REQUIRED >&2;exit 2;fi
# -L also rejects a dangling symlink; never adopt or clean an existing path.
if [ -e "$root" ] || [ -L "$root" ];then echo "HOLD_EXISTING_INSTALL: $root" >&2;exit 3;fi
mkdir -p "${HOME}/.local/share"
stage=$(mktemp -d "${HOME}/.local/share/.daube-ti-messenger.XXXXXXXX")
keep=0
cleanup() {
 rm -f -- "$stage/mcp-list.json" "$stage/mcp-get.json"
 if [ "$keep" = 0 ];then
  # Never unlink the public path: a concurrent replacement cannot be safely
  # removed by a portable readlink-then-unlink sequence. A published payload is
  # retained even if a signal lands just before keep=1.
  if python3 -I - "$root" "$stage" <<'PYKEEP'
import os, sys
root, stage = sys.argv[1:]
sys.exit(0 if os.path.islink(root) and os.readlink(root) == stage + '/repo' else 1)
PYKEEP
  then
   echo "HOLD_PUBLISHED_SOURCE_RETAINED_INSPECT: $root" >&2
  else
   rm -rf -- "$stage"
  fi
 fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP
# Failure to read configuration is not evidence that the name is available.
check_registration_absent() {
 if ! codex mcp list --json > "$stage/mcp-list.json";then
  echo HOLD_CODEX_CONFIG_UNREADABLE >&2;exit 5
 fi
 python3 -I - "$stage/mcp-list.json" <<'PY'
import json, sys
try:
    entries = json.load(open(sys.argv[1]))
    if not isinstance(entries, list) or any(not isinstance(x, dict) or not isinstance(x.get('name'), str) for x in entries):
        raise ValueError('unexpected MCP list shape')
except (OSError, ValueError):
    sys.exit('HOLD_CODEX_CONFIG_UNREADABLE')
if any(x['name'] == 'daube-ti-messenger' for x in entries):
    sys.exit('HOLD_EXISTING_CODEX_MCP_ENTRY_INSPECT_BEFORE_REPLACEMENT')
PY
}
if command -v codex >/dev/null 2>&1;then
 check_registration_absent
fi
git clone --depth 1 --branch "$branch" "$repo" "$stage/repo"
# Hash raw Git blob bytes, then copy ONLY the verified files. Never execute
# clone-local sitecustomize or extra discovered tests. -I ignores PYTHONPATH.
python3 -I - "$stage" <<'PY'
import hashlib, pathlib, sys
stage = pathlib.Path(sys.argv[1])
source = stage / 'repo/integrations/ti-messenger'
pins = {
    'ti_messenger_mcp.py': 'f8d24bf408cad7386966744943781ea6725f4f9d',
    'tests/test_ti_messenger.py': 'cd90975f5d85356324c54fc735c3fd3ff57edabf',
}
verified = {}
for name, expected in pins.items():
    path = source / name
    if path.is_symlink() or not path.is_file():
        sys.exit('HOLD_PINNED_CODE_CHANGED_DO_NOT_REGISTER')
    data = path.read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if actual != expected:
        sys.exit('HOLD_PINNED_CODE_CHANGED_DO_NOT_REGISTER')
    verified[name] = data
for name, data in verified.items():
    target = stage / 'validation' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
PY
python3 -I - "$stage/validation" <<'PY'
import pathlib, py_compile, sys, unittest
root = pathlib.Path(sys.argv[1])
for name in ('ti_messenger_mcp.py', 'tests/test_ti_messenger.py'):
    py_compile.compile(str(root / name), doraise=True)
sys.path.insert(0, str(root))
suite = unittest.defaultTestLoader.discover(str(root / 'tests'), pattern='test_ti_messenger.py')
if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
    sys.exit(4)
PY
echo SOURCE_VALIDATED
# Publish a symlink with no overwrite, atomically, on POSIX. Keep its private
# payload directory on success. os.rename could replace a raced empty directory.
# Install only the verified payload, not the unreviewed cloned files.
rm -rf -- "$stage/repo"
mkdir -p "$stage/repo/integrations/ti-messenger"
cp "$stage/validation/ti_messenger_mcp.py" "$stage/repo/integrations/ti-messenger/ti_messenger_mcp.py"
if command -v codex >/dev/null 2>&1;then
 check_registration_absent
fi
python3 -I - "$root" "$stage/repo" <<'PY'
import os, sys
try:
    os.symlink(sys.argv[2], sys.argv[1])
except FileExistsError:
    sys.exit('HOLD_EXISTING_INSTALL')
PY
keep=1
mcp_file="$root/integrations/ti-messenger/ti_messenger_mcp.py"
if command -v codex >/dev/null 2>&1;then
 # Once add starts, failure/signal may still mean config was written. Retain
 # the payload and report HOLD; never remove config or leave a dangling command.
 keep=1
 if ! codex mcp add daube-ti-messenger -- python3 -I "$mcp_file";then
  echo "HOLD_CODEX_REGISTRATION_UNCERTAIN_INSPECT_CONFIG: $root" >&2;exit 5
 fi
 if ! codex mcp get daube-ti-messenger --json > "$stage/mcp-get.json";then
  echo "HOLD_CODEX_REGISTRATION_READBACK_MISSING_INSPECT_CONFIG: $root" >&2;exit 5
 fi
 if ! python3 -I - "$stage/mcp-get.json" "$mcp_file" <<'PYREAD'
import json, sys
try:
    entry = json.load(open(sys.argv[1]))
    transport = entry['transport']
    if not (entry['name'] == 'daube-ti-messenger'
            and entry['enabled'] is True
            and transport['type'] == 'stdio'
            and transport['command'] == 'python3'
            and transport['args'] == ['-I', sys.argv[2]]):
        raise ValueError('registration differs')
except (OSError, ValueError, KeyError, TypeError):
    sys.exit(5)
PYREAD
 then
  echo "HOLD_CODEX_REGISTRATION_READBACK_MISMATCH_INSPECT_CONFIG: $root" >&2;exit 5
 fi
 echo CODEX_MCP_REGISTERED
else
 keep=1
 echo HOLD_NO_CODEX_CLI_USE_HOSTED_MCP_OR_OTHER_SUPPORTED_CLIENT
fi
echo "MCP_ENTRY: python3 -I $mcp_file"
echo 'Before sending, the Ti cloud secret store must provide the ALREADY AUTHORIZED service identity as DAUBE_TI_CF_ACCESS_CLIENT_ID / DAUBE_TI_CF_ACCESS_CLIENT_SECRET; never paste it in chat/Git.'
echo 'Do not claim LIVE until daube_messenger_audit reads authorized APIs and a separate recipient sends a durable ACK.'
