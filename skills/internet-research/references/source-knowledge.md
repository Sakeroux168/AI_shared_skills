# Source Knowledge and Provenance

`internet-research` is locally authored for `AI_shared_skills`. It does not copy the Agent Reach or OpenCLI Skill text verbatim. The upstream projects provide runtime capability and operational facts; this Skill adds a local research method, evidence model, safety boundary, and graceful-degradation policy.

## Agent Reach

Pinned source:

- repository: `https://github.com/Panniantong/Agent-Reach`
- branch: `main`
- locked commit: `06c202b03400a7d31886bf4399213706da1a0324`
- repository license: MIT
- preserved license: `../../../sources/agent-reach/LICENSE`

Operational points verified against the locked repository documentation:

- Agent Reach is a selector/installer/health-check/router; agents use selected upstream tools directly.
- `agent-reach install --env=auto` is documented as a read-only/check-only safe default.
- system/external installation requires explicit approval.
- OpenCLI is the recommended desktop route for several browser-session platforms.
- Reddit is login-backed rather than a zero-config anonymous path.
- Xiaohongshu OpenCLI usage relies on the user's existing, explicitly controlled browser session; the agent should not perform automatic login or browser-cookie extraction.

The local rights/platform boundary note is:
`../../../sources/agent-reach/snapshot/docs/rights-and-platform-note.md`.

## OpenCLI runtime provenance

Stage 1 accepted this runtime, without vendoring its code:

- repository: `https://github.com/jackwener/OpenCLI`
- tested version: `v1.8.7`
- release-version commit: `87b60a36590c3e2a466c37266c3348d73d7f68fe`
- Browser Bridge extension: `v1.0.23`
- repository license: Apache-2.0

OpenCLI evolves rapidly. Use the installed adapter list/help and current doctor output for exact commands. A newer upstream `main` is not automatically part of this Skill's accepted runtime.

## Rights boundary

The MIT license for Agent Reach and Apache-2.0 license for OpenCLI govern those software projects. They do not relicense:

- third-party posts, comments, replies, videos, subtitles, images, or profile content;
- content from repositories with their own licenses;
- trademarks, likenesses, or platform-owned material;
- user-session data.

Use retrieved material as research evidence, preserve URLs/attribution, quote only what is necessary, and do not infer commercial-use rights from the tooling license.
