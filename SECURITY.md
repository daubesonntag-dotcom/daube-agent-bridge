# Security Policy

## Supported versions
Security fixes target the latest released BRIDGE² version and `main`.

## Reporting a vulnerability
Please do not open a public issue for a vulnerability that could expose credentials, execute unintended commands, or compromise generated integrations.

Until a private security-reporting channel is enabled on GitHub, contact the maintainer through the repository owner's public profile contact path and include a minimal reproduction, affected version, impact, and suggested mitigation when available.

## Security design
- BRIDGE² does not store provider API keys.
- Generated artifacts are text-first and auditable.
- Authentication is delegated to the target host/provider.
- The compiler does not execute generated tool definitions.
- Provider adapters must not claim capabilities unsupported by authoritative documentation.
