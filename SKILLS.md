# Skill Registry

The machine-readable source of truth is [registry/skills.json](registry/skills.json).

| Skill | Category | Local version | Trust | Knowledge source |
|---|---|---:|---|---|
| gpt-image-2-style-library | image generation / prompt engineering | 1.0.0 | trusted | freestylefly/awesome-gpt-image-2 at 685469889fb72fd5adefae45e1645d527edcb5e7 |
| internet-research | research / community intelligence | 0.1.0 | trusted | Agent Reach at 06c202b03400a7d31886bf4399213706da1a0324; OpenCLI v1.8.7 is a verified runtime dependency |

Trust states:

- trusted: source, structure, references, and capability acceptance passed.
- experimental: usable, but at least one required acceptance gate is still pending.
- disabled: retained for provenance but must not be loaded or installed.

`internet-research` completed Windows forward acceptance Scenarios A-D on 2026-08-30 and is bound to `reports/acceptance/2026-08-30-internet-research-v1.md`. A known acceptance-time limitation was recorded: Browser Bridge was disconnected during the graceful-degradation scenario, so that scenario did not obtain a Reddit community sample; prior Stage 1 acceptance had already demonstrated Reddit post/comment retrieval and Browser Bridge connectivity.

A harness should query the registry and load only a matching trusted or explicitly approved experimental skill. It must not preload every skill.
