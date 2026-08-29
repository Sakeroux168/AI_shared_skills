---
name: internet-research
description: Conduct decision-grade multi-source internet and community research using available read-only web, GitHub, Reddit, X/Twitter, Bilibili, Xiaohongshu, comments, replies, and thread backends; use for research, verification, comparison, community sentiment, negative-evidence searches, and requests such as 上网大量查 or 看看社区怎么说.
---

# Internet Research

Produce decision-grade internet research, not a source dump.

## Start with capability health

1. Check the current research capability before relying on a platform. Prefer `agent-reach doctor --json` when Agent Reach is available; use `opencli doctor` before browser-backed reads.
2. Use the backend that is actually healthy in the current environment. Agent Reach is the selector/router; call the selected upstream tool directly.
3. Do not install or repair runtimes, log into accounts, export cookies, or change proxy/TLS/firewall/browser security settings merely to finish a research request. Never export or print cookies merely to make research succeed. Those are separate setup or repair actions.
4. One unavailable platform must not block the entire research task. Record the gap, use independent alternatives, and lower confidence only when the missing evidence is material.
5. Read `references/runtime-contract.md` when platform health, login state, backend choice, or runtime provenance matters.

## Plan the evidence mix

Choose sources for the decision, not to mechanically touch every platform.

- Start with official documentation, primary records, release notes, specifications, or direct statements for factual claims.
- Use GitHub code, commits, Issues, PRs, review comments, and maintainer discussions for implementation reality.
- Use Reddit, X/Twitter, Bilibili, Xiaohongshu, and other relevant communities for experience reports, sentiment, recurring failure modes, and field evidence.
- Read comments, replies, nested replies, or threads when they can materially change interpretation.
- Deliberately search for negative evidence: regressions, incompatibilities, complaints, failed migrations, bans/rate limits, licensing uncertainty, maintenance gaps, and credible counterexamples.

## Research loop

1. Define the decision or question and the claims that must be resolved.
2. Establish authoritative facts and the current version/date context.
3. Gather independent community evidence from the platforms most likely to contain useful firsthand reports.
4. Follow decision-relevant replies and threads instead of stopping at the top-level post.
5. Search for contradictions and disconfirming evidence.
6. Reconcile version, date, environment, and source independence before treating reports as a pattern.
7. Stop at evidence saturation: additional sources no longer change the decision, recurring pattern, meaningful contradiction, confidence level, or important failure mode.

For deeper methodology, read `references/evidence-method.md`.

## Route by capability, not by hard-coded preference

Use what is healthy and appropriate now:

- Web: an available search/reader backend for broad discovery and official pages.
- GitHub: `gh` or an equivalent authenticated read path for repositories, Issues, PRs, comments, reviews, and threads.
- Bilibili: `bili-cli` for search/video/top-level comments; use a healthy browser-backed path when nested replies require it.
- Xiaohongshu: OpenCLI or another approved backend using the user's already logged-in, explicitly controlled browser session.
- Reddit: prefer the healthy login-backed read path. Treat transient 403/429 or anti-bot responses as platform limitations; do not bypass them.
- X/Twitter: use the healthy read backend shown by current capability checks.

Exact command names and adapter options can drift. Inspect installed `--help`, `opencli list`, and doctor output instead of inventing or relying on a stale command catalog.

## Keep an evidence ledger

For important evidence, preserve enough context to audit the conclusion:

- platform and source type;
- author, title, account, repository, or artifact identifier;
- URL or stable identifier when available;
- publication/update date and retrieval date when relevant;
- backend used when runtime behavior matters;
- the claim the evidence supports or contradicts;
- evidence classification and confidence;
- important version/environment qualifiers.

## Distinguish evidence types

Label reasoning internally and make the distinction visible when it matters:

- **Official fact** — primary official documentation, specification, policy, release, or direct statement.
- **Primary technical evidence** — source code, commit, reproducible runtime behavior, Issue/PR discussion, review thread, or first-party artifact.
- **Community report** — user/developer experience, post, video, comment, reply, or discussion.
- **Inference** — synthesis drawn from the evidence above.

Do not turn a viral post into prevalence. Do not count reposts, summaries, or repeated copies of the same underlying claim as independent corroboration.

## Failure handling

- `AUTH_REQUIRED`: ask the user to complete the normal login in their controlled browser only if that platform is necessary. Never auto-login.
- Browser Bridge disconnected: report the manual prerequisite; do not work around the browser security boundary.
- HTTP 403/429 or platform security page: allow only ordinary low-impact retry behavior already provided by the official backend. If it persists, record the limitation and continue elsewhere.
- HTML/JSON mismatch or adapter breakage: treat it as a backend limitation. Do not patch upstream source code inside an ordinary research task.
- GitHub credential/keyring context differs across execution environments: distinguish host authentication from the current agent process; do not claim the account is broken without evidence.
- Do not modify system TLS, firewall, proxy, certificate, browser security, or anti-bot controls unless the user separately authorizes a narrowly scoped repair task.

## Default permission boundary

**READ ONLY by default.**

Allowed without extra confirmation when available:
- search, open, fetch, and read public or user-authorized content;
- read repositories, Issues, PRs, comments, reviews, and threads;
- read posts, profiles, comments, replies, subtitles, and other research evidence.

Require explicit user confirmation before any write or account-changing action, including:
- post, publish, comment, reply, review, message;
- like, react, follow, save, favorite;
- create, update, delete, merge, or submit;
- login, credential configuration, cookie export/import, or other authentication changes.

Never autonomously perform payment, account-security changes, irreversible actions, or attempts to bypass platform protections.

## Final answer

Lead with the decision or research conclusion, then provide the evidence that matters:

1. authoritative/current facts;
2. community and field evidence;
3. meaningful disagreements, failures, and negative evidence;
4. conclusion with confidence;
5. limitations, missing platforms, stale evidence, or unresolved contradictions;
6. citations or links that let the reader verify the important claims.

Keep official facts, community sentiment, and inference separate. Do not hide a material platform failure or evidence gap behind a confident summary.
