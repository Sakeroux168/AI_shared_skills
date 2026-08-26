# Source Registry

The machine-readable source of truth is [registry/sources.json](registry/sources.json).

| Source | Branch | Locked commit | Repository license | Third-party content rights | Sync mode |
|---|---|---|---|---|---|
| freestylefly/awesome-gpt-image-2 | main | 685469889fb72fd5adefae45e1645d527edcb5e7 | Upstream declares MIT | Separate or unknown; commercial use not guaranteed | review-driven |

At the current locked commit, the curated snapshot contains the upstream Skill package, 529 case
prompts, 22 templates, 13 categories, 19 style tags, 10 scene tags, required covers, the
[upstream disclaimer](sources/awesome-gpt-image-2/snapshot/docs/disclaimer.md), and source
generation/install scripts. These totals describe the current lock; they are not validation
constants. Future changes are recorded as previous/new/delta values in the sync report.

The website, API, billing code, and hundreds of nonessential gallery binaries are not vendored.
Every case image is pinned by Git blob SHA and immutable raw URL in case-images.lock.json and can be
hydrated during a reviewed sync.

The MIT record describes the license declared for the upstream repository. It is not a uniform
rights declaration for community-sourced prompts, generated images, trademarks, likenesses, or
referenced works. Preserve case attribution and source-specific terms; obtain authorization from
the applicable rights holder before commercial use.
