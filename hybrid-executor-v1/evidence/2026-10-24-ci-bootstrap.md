# Hybrid Executor v1 — GitHub CI bootstrap evidence (2026-10-24)

PR #31 (`ci/hybrid-v1-default-bootstrap-20261024`) merged the isolated Hybrid workflow only to `main`, at commit `0f89a70b5859395d06a2fbde108fbad309eda4c7`.

Independent GCP exact-SHA validation of the CI-only PR before merge: file scope and read-only controls checked, YAML parsed successfully, exit code 0. The bootstrap contains a single workflow YAML, identical to the file in this Hybrid PR.

This evidence commit is an intentional PR synchronizing change to observe whether GitHub Actions now triggers after the workflow exists on the default branch. It does **not** authorize merging Hybrid PR #30, executing production changes, or bypassing required status checks.

Gate: HOLD until GitHub returns a real run and exact-HEAD check result. Runtimes must be verified against this new HEAD after the commit.
