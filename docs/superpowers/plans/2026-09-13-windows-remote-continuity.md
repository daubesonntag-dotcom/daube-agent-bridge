# Windows Remote Continuity Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make D'AUBE's Windows remote-control plane survive lock-screen operation and Remote Desktop Commander v0.2.50 restarts without duplicate launchers, refresh-token replay failure, or `npx` restart storms.

**Architecture:** Tailscale, OpenSSH, and RustDesk remain the service-plane recovery path. Desktop Commander becomes one best-effort interactive lane with a single Scheduled Task owner. The owner launches a pinned local install directly with Node, applies an idempotent v0.2.50 session-persistence workaround before launch, and leaves OfficeAgent in observe-only mode for Desktop Commander.

**Tech Stack:** Windows PowerShell 5.1+, Task Scheduler, Node.js 18+, Desktop Commander 0.2.50, Tailscale/OpenSSH/RustDesk.

**Spec:** Root cause evidence from upstream DesktopCommanderMCP issue #695 plus D'AUBE workstation soak evidence on 2026-09-13.

## Global Constraints

- Zero paid dependencies.
- No secrets, tokens, device IDs, or user data in repository files or logs.
- Fail closed on unknown Desktop Commander versions or unknown patch anchors.
- Do not replace Tailscale, OpenSSH, or RustDesk; they remain native Windows services.
- Exactly one Desktop Commander launch owner.
- Rollback artifacts must be written before Scheduled Task or OfficeAgent ownership changes.

---

### Task 1: Token-persistence patcher

**Files:**
- Create: `ops/windows/remote-continuity/patch-device-persistence.mjs`
- Create: `ops/windows/remote-continuity/patch-device-persistence.test.mjs`

**Interfaces:**
- Consumes: compiled `dist/remote-device/device.js` from Desktop Commander 0.2.50.
- Produces: `patchDeviceSource(source: string): string` and CLI patching of one file path.

- [ ] Write tests proving the patch is inserted after `startHeartbeat`, is idempotent, and refuses unknown builds.
- [ ] Run `node --test ops/windows/remote-continuity/patch-device-persistence.test.mjs` and verify RED before implementation.
- [ ] Implement only the guarded five-minute session persistence timer required by upstream issue #695.
- [ ] Re-run the Node test and verify all tests PASS.

### Task 2: Deterministic local launcher

**Files:**
- Create: `ops/windows/remote-continuity/launch-desktop-commander.ps1`

**Interfaces:**
- Consumes: `%LOCALAPPDATA%\Daube\desktop-commander\node_modules\@wonderwhy-er\desktop-commander`.
- Produces: one long-lived Desktop Commander remote process launched by absolute Node and package paths.

- [ ] Verify package version is exactly `0.2.50`; fail closed otherwise.
- [ ] Apply Task 1 patcher to `dist\remote-device\device.js`.
- [ ] Launch `dist\index.js remote` directly; never invoke `npx` on the steady-state path.
- [ ] Propagate the child exit code to Task Scheduler.

### Task 3: Single-owner installer

**Files:**
- Create: `ops/windows/remote-continuity/install.ps1`
- Create: `ops/windows/remote-continuity/rollback.ps1`

**Interfaces:**
- Consumes: existing OfficeAgent at `%LOCALAPPDATA%\Daube\office-agent` and current Scheduled Tasks.
- Produces: `Daube-OfficeAgent-Supervisor` and `Daube-DesktopCommander-Watchdog` with `IgnoreNew` semantics.

- [ ] Back up OfficeAgent config and exported task XML before mutation.
- [ ] Ensure pinned Desktop Commander 0.2.50 exists locally; install only when absent.
- [ ] Set OfficeAgent `desktopCommander.enabled=false` so it observes but cannot spawn Desktop Commander.
- [ ] Create/update `Daube-OfficeAgent-Supervisor` to run only `supervisor.ps1`.
- [ ] Create/update `Daube-DesktopCommander-Watchdog` to run only the deterministic launcher.
- [ ] Disable legacy duplicate `D_AUBE_OfficeSupervisor_User` without deleting it.
- [ ] Start canonical tasks and emit a machine-readable install receipt.
- [ ] Implement rollback from the most recent backup receipt.

### Task 4: Verification gate

**Files:**
- Create: `.github/workflows/windows-continuity.yml`

**Interfaces:**
- Consumes: Task 1-3 scripts.
- Produces: PR gate for Node behavior tests and PowerShell parser validation.

- [ ] Run the Node patcher test on `windows-latest` with Node 22.
- [ ] Parse every PowerShell file with `System.Management.Automation.Language.Parser` and fail on syntax errors.
- [ ] Open a PR and require the Windows continuity workflow to pass before rollout.

### Task 5: Workstation rollout and soak

**Files:** none in repository.

- [ ] When `DESKTOP-30OFU23` reconnects, run `install.ps1` from this exact branch revision.
- [ ] Verify one OfficeAgent supervisor and one Desktop Commander root tree.
- [ ] Verify Tailscale, `sshd`, and RustDesk remain `Running / Auto / LocalSystem`.
- [ ] Lock the workstation and keep the display off for at least two Desktop Commander heartbeat/recovery cycles.
- [ ] Restart only the Desktop Commander task after the stored access token has rotated; verify `Found persisted session` reaches `Device ready` without browser authorization.
- [ ] Mark production PASS only when no duplicate process tree, no `Invalid Refresh Token: Already Used`, and remote tool execution all remain green.