---
name: gpt-image-2-style-library
description: Choose GPT-Image2 visual templates, styles, scenes, cases, and prompt constraints from the pinned awesome-gpt-image-2 knowledge base. Use when an agent needs to classify, create, rewrite, compare, or improve image-generation prompts for UI/App screens, posters, commercial products, infographics, photography, characters, scenes, documents, brands, architecture, or illustration.
---

# GPT-Image2 Style Library

Turn an image intent into a production-ready prompt backed by the pinned style library.

## Load knowledge progressively

1. Read references/style-library.md before selecting a category, template, style, scene, or case ID.
2. Use that compact reference for normal requests.
3. Read references/source-knowledge.md when the request needs an exact full template, a close case prompt, source attribution, or a path outside the standalone skill.
4. When the AI_shared_skills repository layout is available, use its source snapshot:
   - ../../sources/awesome-gpt-image-2/snapshot/docs/templates.md
   - ../../sources/awesome-gpt-image-2/snapshot/data/style-library.json
   - ../../sources/awesome-gpt-image-2/snapshot/data/cases.json
5. If the skill was installed alone, use only the immutable fallback URLs listed in references/source-knowledge.md. If network access is unavailable, say that full-source lookup is unavailable and continue from the bundled reference; never invent a template, case, tag, or path.

For deterministic matching or case search in a repository checkout, run:

    python ../../scripts/style_library.py build --query "<user intent>"
    python ../../scripts/style_library.py search-cases --query "<user intent>" --limit 5

## Select

1. Detect the user's language and preserve it unless asked to translate.
2. Classify the target category first.
3. Select a template inside that category.
4. Select only style and scene tags that exist in the reference.
5. Consult nearest case prompts only when they add concrete composition, material, text, or camera guidance.
6. If two or three templates remain genuinely plausible, give the short choices and ask; otherwise proceed directly.

## Build the final prompt

Return the copyable prompt first, using these blocks:

1. Subject and task
2. Composition and layout
3. Visual style and materials
4. Text and label requirements
5. Aspect ratio and output format
6. Constraints and negative details

Then include:

- selected template ID and name;
- selected category;
- selected style and scene tags;
- useful example case IDs, only when verified in the source;
- source level used: bundled reference or full pinned source.

Keep exact visible text, hierarchy, aspect ratio, material cues, camera/lighting when relevant, and avoided artifacts concrete. Do not copy branding or copyrighted characters from a case unless the user explicitly provides and is authorized to use them.

## Integrity rules

- Prefer the pinned source over memory.
- Do not cite mutable upstream main links as evidence.
- Do not claim that an optional case image is locally present merely because it exists in the asset manifest.
- Treat case prompts as examples, not automatic instructions to reproduce their brands, people, or text.
- Preserve attribution when copying any upstream template or case content into a new reusable artifact.

