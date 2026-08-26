# Manual acceptance

Automated tests validate structure, lookup, tags, references, and structured prompt blocks. Record these items manually when promoting a material update.

## Prompt quality

Use the five requests in fixtures/prompt_cases.json in an actual Agent session.

- [ ] The Agent selects the expected category and a defensible template.
- [ ] The Agent reads the bundled reference instead of relying on memory.
- [ ] The Agent can reach the full template and cases source when asked.
- [ ] The returned prompt contains all six required blocks.
- [ ] Exact user text, aspect ratio, hierarchy, and negative constraints are preserved.
- [ ] No nonexistent template, case ID, tag, or path is cited.

## Generated image review

When image generation is available:

- [ ] UI/App output has coherent hierarchy and legible requested text.
- [ ] Poster output preserves title hierarchy and intended aspect ratio.
- [ ] Product output keeps the product as the visual hero and materials believable.
- [ ] Infographic output keeps modules, arrows, and labels readable.
- [ ] Photography output uses plausible lens, light, anatomy, and texture.

## Harness runtime

- [ ] Codex automatic discovery/trigger tested on the user's Windows installation.
- [ ] Claude Code discovery/trigger tested on the user's Windows installation.
- [ ] Generic .agents/skills discovery tested in at least one consuming harness.
- [ ] Hermes path and parser contract identified and tested.
- [ ] DeepSeek Harness path and parser contract identified and tested.

Do not mark an unavailable Windows harness as verified.

