# Runtime Contract

This reference records the runtime boundary accepted before the `internet-research` Skill was introduced. It is provenance and routing guidance, not an instruction to install or mutate the host.

## Pinned Agent Reach source

- Repository: `https://github.com/Panniantong/Agent-Reach`
- Branch: `main`
- Locked source commit: `06c202b03400a7d31886bf4399213706da1a0324`
- Repository license at that commit: MIT, Copyright (c) 2025 Agent Eyes
- Windows runtime exercised during Stage 1: Agent Reach `v1.5.0`

At the locked source, Agent Reach documents itself as the selector, installer, health checker, and router. Research agents should use the selected upstream tools directly rather than treating Agent Reach as a content-fetching wrapper.

## Verified OpenCLI runtime dependency

The Stage 1 Windows acceptance exercised:

- OpenCLI `v1.8.7`
- Release-version commit: `87b60a36590c3e2a466c37266c3348d73d7f68fe`
- OpenCLI Browser Bridge extension `v1.0.23`
- Repository license: Apache-2.0, Copyright 2025 jackwener

OpenCLI is a runtime dependency for browser-session research in this Skill; its source code is not vendored into `AI_shared_skills`.

OpenCLI `main` moves independently and may be newer than the accepted `v1.8.7` runtime. Never treat a newer upstream `main` commit as accepted merely because it exists. Re-run the relevant acceptance before updating this contract.

## Stage 1 capability evidence

Real read-only Windows retrieval was completed before this Skill was registered:

- Web: real broad-web content.
- GitHub: repository content plus real Issue/PR comments and PR review comments/threads.
- Bilibili: video metadata, top-level comments, and nested replies.
- X/Twitter: tweets, threads, and replies.
- Xiaohongshu: note content, comments, and nested replies using the user's existing logged-in browser session.
- Reddit: post/comment reads. A temporary HTTP 403 / network-security anti-bot response occurred during acceptance and later recovered without bypassing platform controls.
- Browser Bridge: daemon, extension, and connectivity were stable across fresh Windows shells.

This proves runtime feasibility. It does **not** by itself promote the new `internet-research` Skill from `experimental` to `trusted`; the Skill still needs forward acceptance.

## Browser-session boundary

For session-backed platforms:

- reuse only a browser session that the user already controls and has logged into;
- never auto-fill passwords, one-time codes, or 2FA;
- never export or print cookies merely to make research succeed;
- if login is missing, report the manual prerequisite;
- if platform security blocks access, degrade gracefully instead of bypassing controls.

## Command drift

Agent Reach and OpenCLI evolve quickly. Before executing a platform read:

1. inspect current `agent-reach doctor --json` or equivalent health output;
2. inspect `opencli doctor` for browser-backed work;
3. inspect installed `--help` / `opencli list` when exact syntax matters;
4. prefer observed runtime capability over remembered command names.

Do not embed a large frozen command catalog in this Skill.
