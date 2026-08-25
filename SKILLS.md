# Skill Registry

The machine-readable source of truth is [registry/skills.json](registry/skills.json).

| Skill | Category | Local version | Trust | Knowledge source |
|---|---|---:|---|---|
| gpt-image-2-style-library | image generation / prompt engineering | 1.0.0 | trusted | freestylefly/awesome-gpt-image-2 at 685469889fb72fd5adefae45e1645d527edcb5e7 |

Trust states:

- trusted: source, structure, references, and capability acceptance passed.
- experimental: usable, but at least one required acceptance gate is still pending.
- disabled: retained for provenance but must not be loaded or installed.

A harness should query the registry and load only a matching trusted or explicitly approved experimental skill. It must not preload every skill.
