# AI_shared_skills

A review-driven registry of reusable professional Agent skills and their pinned source knowledge bases.

This repository answers **what an Agent can do**. It is intentionally separate from [Sakeroux168/AI_chat_skill](https://github.com/Sakeroux168/AI_chat_skill), which answers **how Agents collaborate**: requirements, routing, engineering discipline, review, and PR delivery.

## V1 status

Two professional capabilities are now registered and trusted:

- `gpt-image-2-style-library` — trusted; derived from `freestylefly/awesome-gpt-image-2` and pinned to commit `685469889fb72fd5adefae45e1645d527edcb5e7`.
- `internet-research` — trusted; locally authored decision-grade research workflow backed by pinned Agent Reach provenance at `06c202b03400a7d31886bf4399213706da1a0324` and the accepted OpenCLI v1.8.7 Windows runtime.

The integration has two layers:

- `skills/`: small installable skills loaded only when a matching capability is needed.
- `sources/`: pinned provenance/knowledge records used for exact source knowledge, rights metadata, and reviewed updates.

    AI_shared_skills/
    ├── registry/              machine-readable skill/source discovery
    ├── skills/                installable, context-efficient skills
    ├── sources/               pinned and attributed source knowledge/provenance
    ├── scripts/               query, install, validate, detect, sync
    ├── tests/                 automated and manual acceptance
    ├── docs/                  compatibility and operating guides
    └── .github/workflows/     CI and review-only upstream sync PRs

## Discover and use a skill

1. Search [registry/skills.json](registry/skills.json) by capability, category, or status. The registry is an extensible array: each Skill is validated independently against its Source and lock.
2. Load only the selected Skill's `SKILL.md`.
3. Use its compact bundled references for normal work.
4. Read deeper source knowledge only when the task needs it.

A `trusted` Skill is deployable by default. An `experimental` Skill requires explicit approval until its remaining acceptance gate is complete. A `disabled` Skill must not be loaded.

Example deterministic image lookup:

    python scripts/style_library.py build --query "为手机银行设计深色仪表盘 UI" --aspect-ratio 9:16

Example isolated installation:

    python scripts/install_skill.py gpt-image-2-style-library --target agents

The installer copies files. It never creates junctions or symlinks, and it refuses to replace an existing installation unless `--force` is supplied; forced replacement first preserves a timestamped backup.

## internet-research

`internet-research` is for requests such as “上网大量查一下”, “看看社区怎么说”, decision support, verification, comparison, community sentiment, and finding real-world failure reports.

Its default workflow is:

1. establish official/current facts;
2. inspect primary technical evidence such as GitHub code, Issues, PRs, comments, reviews, and threads when relevant;
3. gather independent field evidence from relevant communities such as Reddit, X/Twitter, Bilibili, and Xiaohongshu;
4. read decision-relevant comments/replies instead of stopping at the parent post;
5. deliberately search for negative evidence and contradictions;
6. distinguish official facts, primary technical evidence, community reports, and inference;
7. stop at evidence saturation rather than collecting redundant links;
8. degrade gracefully if one platform/backend is unavailable.

The Skill is **READ ONLY by default**. Posting, commenting, reacting, following, saving, publishing, account changes, login/credential changes, or other writes require explicit user confirmation. It does not auto-login, export cookies, or bypass platform/network security to make a research task pass.

Stage 1 Windows acceptance proved real read-only retrieval for Web, GitHub, Bilibili, X/Twitter, Xiaohongshu, Reddit, comments/replies, and OpenCLI Browser Bridge stability. On 2026-08-30 the Skill then passed forward-acceptance Scenarios A-D plus automated validation and was promoted to `trusted`; the acceptance record is [reports/acceptance/2026-08-30-internet-research-v1.md](reports/acceptance/2026-08-30-internet-research-v1.md). The forward-acceptance report also records the observed limitation that Browser Bridge was disconnected during Scenario C, so that scenario demonstrated graceful degradation without obtaining a Reddit community sample.

## Controlled upstream updates

Upstream changes never overwrite `main`.

For `gpt-image-2-style-library`, the supported synchronization flow remains:

1. compare the locked commit with upstream main;
2. create a `sync/...` branch;
3. refresh only the reviewed snapshot allowlist and generated indexes;
4. automatically downgrade affected Skills to experimental when the commit changes;
5. run structural, rights-metadata, and prompt acceptance tests;
6. write a sync report with previous/new knowledge counts and deltas;
7. open a draft PR;
8. complete required manual acceptance and explicitly promote the Skill in a reviewed commit;
9. merge manually, then treat the new commit as locked.

The existing `check_upstream.py` / `sync_upstream.py` pipeline is specialized to the image source. Agent Reach uses the review strategy recorded in `registry/sources.json` until a generic multi-source synchronizer is intentionally introduced; this V1 does not invent one speculatively.

## Validation

    python scripts/validate_repository.py
    python -m unittest discover -s tests -v

Automated validation covers registry/source contracts, trust policy, installation behavior, the image capability, and the `internet-research` structure/safety/attestation contract. Research quality is additionally governed by [tests/internet-research-manual-acceptance.md](tests/internet-research-manual-acceptance.md) and its recorded forward-acceptance report.

## Licensing

The awesome-gpt-image-2 upstream repository declares MIT and its license text is preserved, but this repository does not treat that declaration as blanket permission for every community-sourced prompt, generated image, trademark, likeness, or referenced work.

Agent Reach is pinned with its upstream MIT license preserved at [sources/agent-reach/LICENSE](sources/agent-reach/LICENSE). OpenCLI v1.8.7 is a non-vendored runtime dependency whose upstream repository uses Apache-2.0. Neither software license relicenses third-party content retrieved from websites, social platforms, repositories, comments, media, or user sessions.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), [SOURCES.md](SOURCES.md), and each source's recorded rights metadata. No repository-wide license for locally authored files is asserted by this V1.

## Relationship with AI_chat_skill

`AI_chat_skill` remains the lightweight collaboration/routing layer and keeps its ten V1.1 global skills. It discovers professional capabilities through this repository's metadata-driven registry rather than hard-coding image, research, or platform backends.

`internet-research` is therefore a professional capability in `AI_shared_skills`; it does **not** add an eleventh global collaboration Skill to `AI_chat_skill`.
