# Source Registry

The machine-readable source of truth is [registry/sources.json](registry/sources.json).

| Source | Branch | Locked commit | License | Sync mode |
|---|---|---|---|---|
| freestylefly/awesome-gpt-image-2 | main | 685469889fb72fd5adefae45e1645d527edcb5e7 | MIT | review-driven |

The curated snapshot contains the upstream skill package, the complete 529-case prompt dataset, the 22-template library, structured category/style/scene data, required template covers, and source generation/install scripts. The website, API, billing code, and hundreds of nonessential gallery binaries are not vendored. Every case image is still pinned by Git blob SHA and immutable raw URL in case-images.lock.json, and can be hydrated during a reviewed sync.

