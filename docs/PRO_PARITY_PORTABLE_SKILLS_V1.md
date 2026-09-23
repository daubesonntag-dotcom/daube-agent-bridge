# Pro-Parity Portable Skills V1

BRIDGE² carries observable workflow discipline across agent ecosystems without copying private provider prompts or hidden reasoning.

## Optional semantic fields

Portable skill specs now support:

- instructions: ordered provider-neutral operating instructions.
- required_capabilities: capability names the runtime must satisfy before executing the skill.

Both fields are optional, so legacy v0.1.x skill specs remain valid.

The compiler emits these fields into the canonical bridge manifest and renders them into SKILL.md surfaces. Tool/function schemas remain unchanged.

## Canonical fixtures

The Pro-parity fixture set covers:

- research: scope, search, read, cross-check, cite, verify;
- coding: inspect, reproduce, edit, test, review;
- browser: observe, act, verify, recover;
- runtime recovery: independent verification, checkpoint/resume, schema repair, provider failover.

The same canonical spec compiles deterministically into all existing BRIDGE² target families. Unsupported runtime capabilities remain a deployment/admission concern; generated artifacts must never imply a provider has a capability it does not actually expose.

## Security boundary

Instructions are D’AUBE-owned portable workflow policy. They must not contain secrets, proprietary hidden prompts, or copied private provider instructions.
