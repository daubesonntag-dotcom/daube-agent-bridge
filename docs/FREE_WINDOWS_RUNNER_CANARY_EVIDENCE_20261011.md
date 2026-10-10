# D'AUBE Public Windows Runner Canary — blocked before VM allocation

## Target
Proof of a laptop-independent Windows cloud VM using the standard GitHub-hosted
`windows-2025` runner of this public repository. This VM class would normally
be free for public repositories using standard runners according to GitHub Docs.

## Actual test — 2026-10-10 UTC

- Repository: `daubesonntag-dotcom/daube-agent-bridge` (public).
- Branch: `feat/free-windows-runner-v1`.
- Source commit: `bf4950b477a1b5a31efdafd014e32cd4ba9692ef`.
- Workflow: `.github/workflows/daube-free-windows-vm-canary.yml`.
- Workflow run: https://github.com/daubesonntag-dotcom/daube-agent-bridge/actions/runs/38071175520
- Job ID: `114268721763`.
- GitHub Actions result: `failure`, job count 1, zero steps, runner name empty.
- GitHub CLI **annotation**:

  `The job was not started because your account is locked due to a billing issue.`

This is **conclusive for this specific test**: no Windows VM was allocated,
`where.exe` was not executed, and the `DAUBE_WINDOWS_EXEC_OK` marker was
not produced. Do not count this as a Windows proof.

The workflow contains no secrets, third-party actions, or private repository
source checkout. It only checks a built-in Windows executable and SHA-256 digest.

## Root-cause and recovery

The exact GitHub annotation indicates an **account-level billing lock** for
hosted job admission, not a failed PowerShell script. The same symptom on
other repositories should be investigated using their own run annotations,
rather than assuming a uniform root cause without evidence.

The account owner must review the official GitHub Billing settings and
resolve the billing lock. No payment method, charge, budget limit or GitHub
account payment configuration has been changed by D'AUBE.

After the account lock is resolved, re-run the exact SHA-pinned canary and
require the following before promotion: Windows runner populated, at least
one executed step, `DAUBE_WINDOWS_EXEC_OK`, SHA-256 output, and an actual
successful job verdict. A successful public Windows canary would prove
ephemeral executable execution — not a persistent Windows cloud desktop.

Official standard-runner reference:
https://docs.github.com/en/actions/reference/runners/github-hosted-runners

## Current decision

`WINDOWS_EXE_CLOUD_ON_DEMAND = BLOCKED_BY_GITHUB_BILLING_LOCK`.
`FULL_REMOTE_LIVE_FINAL = NOT_CLAIMED`.
