# Source Registry

The machine-readable source of truth is [registry/sources.json](registry/sources.json).

| Source | Branch | Locked commit | Repository license | Third-party content rights | Sync mode |
|---|---|---|---|---|---|
| freestylefly/awesome-gpt-image-2 | main | 685469889fb72fd5adefae45e1645d527edcb5e7 | Upstream declares MIT | Separate or unknown; commercial use not guaranteed | review-driven |
| Panniantong/Agent-Reach | main | 06c202b03400a7d31886bf4399213706da1a0324 | MIT | Mixed: tool/repository license does not relicense retrieved platform content | review-driven |

At the current awesome-gpt-image-2 lock, the curated snapshot contains the upstream Skill package, 529 case
prompts, 22 templates, 13 categories, 19 style tags, 10 scene tags, required covers, the
[upstream disclaimer](sources/awesome-gpt-image-2/snapshot/docs/disclaimer.md), and source
generation/install scripts. These totals describe the current lock; they are not validation
constants. Future changes are recorded as previous/new/delta values in the sync report.

The website, API, billing code, and hundreds of nonessential gallery binaries are not vendored.
Every case image is pinned by Git blob SHA and immutable raw URL in case-images.lock.json and can be
hydrated during a reviewed sync.

The Agent Reach source snapshot is intentionally minimal: it preserves pinned provenance, the
upstream MIT license, and the local platform-content rights boundary used by `internet-research`.
The Agent Reach executable/runtime is installed independently on the user's machine and is not
vendored into this repository.

OpenCLI is also not vendored in V1. The accepted Windows runtime dependency for the new Skill is
OpenCLI v1.8.7 at release-version commit `87b60a36590c3e2a466c37266c3348d73d7f68fe`, with Browser Bridge extension
v1.0.23. A newer OpenCLI `main` is not automatically accepted; runtime guidance must be reviewed
and re-tested before this record changes.

Software licenses describe Agent Reach/OpenCLI themselves. They do not grant rights to third-party
posts, comments, replies, videos, subtitles, repositories, trademarks, likenesses, or other
platform content retrieved during research. Preserve evidence URLs and attribution and follow the
originating source's license and platform terms.

The MIT record for awesome-gpt-image-2 likewise is not a uniform rights declaration for
community-sourced prompts, generated images, trademarks, likenesses, or referenced works. Preserve
case attribution and source-specific terms; obtain authorization from the applicable rights holder
before commercial use.
