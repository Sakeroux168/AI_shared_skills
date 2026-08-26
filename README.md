# AI_shared_skills

A review-driven registry of reusable professional Agent skills and their pinned source knowledge bases.

This repository answers **what an Agent can do**. It is intentionally separate from [Sakeroux168/AI_chat_skill](https://github.com/Sakeroux168/AI_chat_skill), which answers **how Agents collaborate**: requirements, routing, engineering discipline, review, and PR delivery.

## V1 status

The first integrated capability is gpt-image-2-style-library, derived from [freestylefly/awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) and pinned to commit 685469889fb72fd5adefae45e1645d527edcb5e7 on main.

The integration has two layers:

- skills/: the small installable skill loaded by an Agent.
- sources/: the pinned source knowledge base used for exact templates, all case prompts, structured tags, generation tooling, attribution, and optional assets.

    AI_shared_skills/
    ├── registry/              machine-readable skill/source discovery
    ├── skills/                installable, context-efficient skills
    ├── sources/               pinned and attributed source knowledge
    ├── scripts/               query, install, validate, detect, sync
    ├── tests/                 automated and manual acceptance
    ├── docs/                  compatibility and operating guides
    └── .github/workflows/     CI and review-only upstream sync PRs

## Discover and use a skill

1. Search [registry/skills.json](registry/skills.json) by capability, category, or status. The
   registry is an extensible array: each Skill is validated independently against its Source and
   lock; the repository is not limited to one Skill.
2. Load only the selected skill's SKILL.md.
3. Use its compact bundled reference for normal work.
4. Read the linked source knowledge only when exact templates or cases are needed.

Example deterministic lookup:

    python scripts/style_library.py build --query "为手机银行设计深色仪表盘 UI" --aspect-ratio 9:16

Example isolated installation:

    python scripts/install_skill.py gpt-image-2-style-library --target agents

The installer copies files. It never creates junctions or symlinks, and it refuses to replace an existing installation unless --force is supplied; forced replacement first preserves a timestamped backup.

## Controlled upstream updates

Upstream changes never overwrite main. The supported flow is:

1. compare the locked commit with upstream main;
2. create a sync/... branch;
3. refresh only the reviewed snapshot allowlist and generated indexes;
4. automatically downgrade every affected Skill to experimental when the commit changes;
5. run structural, rights-metadata, and prompt acceptance tests;
6. write a sync report containing previous/new knowledge counts and deltas;
7. open a draft PR for review;
8. complete required manual acceptance and explicitly promote the Skill in a reviewed commit;
9. merge manually, then treat the new commit as locked.

Template, category, style, scene, and case totals are observed upstream inventory, not permanent
validation constants. Changes appear in the sync report for Review; broken structure, references,
source locks, manifests, or attribution still fail validation.

Run detection locally with:

    python scripts/check_upstream.py --json

See [MAINTENANCE.md](MAINTENANCE.md) for the manual workflow and [the sync workflow](.github/workflows/sync-upstream.yml) for the scheduled draft-PR implementation. No workflow enables auto-merge.

## Validation

    python scripts/validate_repository.py
    python -m unittest discover -s tests -v

Automated acceptance covers UI/App, poster, product/commercial, infographic, and realistic photography requests. Visual quality after actual image generation and Windows harness discovery remain manual checks; see [tests/manual-acceptance.md](tests/manual-acceptance.md) and [docs/WINDOWS.md](docs/WINDOWS.md).

## Licensing

The upstream repository declares MIT and its license text is preserved, but this repository does
not treat that declaration as blanket permission for every community-sourced prompt, generated
image, trademark, likeness, or referenced work. Those elements may have separate or unknown
rights, and upstream does not guarantee commercial usability. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md), the preserved
[upstream disclaimer](sources/awesome-gpt-image-2/snapshot/docs/disclaimer.md), and the
source-specific [repository license](sources/awesome-gpt-image-2/LICENSE). No repository-wide
license for locally authored files is asserted by this V1.

## Relationship with AI_chat_skill

AI_chat_skill remains the lightweight collaboration/routing layer and keeps its ten V1.1 global skills. It should discover professional capabilities through this repository's registry rather than hard-code mappings such as image → one skill or video → another skill. V1 does not copy this professional skill into AI_chat_skill.
