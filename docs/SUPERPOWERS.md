# Superpowers integration

D'AUBE BRIDGE² can adopt [obra/superpowers](https://github.com/obra/superpowers)
without rewriting upstream skill bodies.

## What the bootstrap does

`daube-bridge superpowers --project <path>`:

1. fetches the requested upstream Git ref without running upstream scripts;
2. copies only discovered `skills/*/SKILL.md` bundles into
   `<project>/.agents/skills`;
3. adds an idempotent D'AUBE block to `<project>/AGENTS.local.md` so
   DeepSeek Harness and other AGENTS-aware runners check the native skill catalog
   before implementation;
4. preserves the upstream license and writes the resolved commit to
   `<project>/.daube/superpowers/lock.json`;
5. when Gemini CLI is installed, uses Gemini's native extension command to install
   or update the official Superpowers extension.

Use `--skip-gemini` when the project only needs the portable skill layer.

## Why project scope

DeepSeek Harness discovers project skills from both `.dsh/skills` and
`.agents/skills`. D'AUBE uses `.agents/skills` because it is portable across
multiple agent ecosystems. Harness also loads project `AGENTS.md` and
`AGENTS.local.md` instructions, making the local bootstrap deterministic without
editing user-global configuration.

The bootstrap refuses to overwrite a same-named skill unless that directory was
previously marked as D'AUBE-managed.

## Verification

After bootstrap, start a clean agent session and ask:

> Let's make a React todo list.

Expected behavior: the agent loads `using-superpowers` / `brainstorming` before
writing implementation code. A missing native capability must degrade explicitly;
the agent must not fabricate a tool call.

## Upstream boundary

Superpowers remains an independent upstream project. D'AUBE stores the source URL,
requested ref, resolved commit, copied skill names, and license with each install.
D'AUBE does not silently edit upstream `SKILL.md` bodies.
