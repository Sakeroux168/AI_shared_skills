# awesome-gpt-image-2 source knowledge

This directory manages the pinned knowledge source for the active gpt-image-2-style-library skill.

## Included

- The upstream skill package and its generated compact reference.
- The complete structured style library: 22 templates, 13 categories, 19 style tags, and 10 scene tags at the locked commit.
- The complete cases.json dataset with 529 case prompts.
- The full industrial template document.
- The upstream generator/install scripts and publish workflow.
- Every category cover and template cover needed to run the upstream generator.

## Managed without default vendoring

The remaining case images are optional visual examples. case-images.lock.json records every case ID, image path, Git blob SHA, and immutable raw URL. Pass --with-case-images to the sync script only when a reviewed branch intentionally hydrates the full binary gallery.

## Provenance and modifications

The upstream snapshot is copied without silent edits. The active skill is a local integration layer: it adds source discovery, pinned fallbacks, deterministic query tooling, and repository tests. See ../../THIRD_PARTY_NOTICES.md and source.lock.json.

