# Maintenance

## Review-driven update

1. Start from the latest main and create sync/gpt-image-2-style-library-<short-sha>.
2. Run python scripts/check_upstream.py --json.
3. Run python scripts/sync_upstream.py --to-commit <full-sha> on the sync branch.
4. Inspect the curated snapshot, active skill diff, attribution, and generated report under reports/sync/.
5. Run python scripts/validate_repository.py and python -m unittest discover -s tests -v.
6. Complete tests/manual-acceptance.md when the change affects matching, prompt structure, images, or harness behavior.
7. Commit only the listed integration paths, push the sync branch, and open a draft PR.
8. Review and merge manually. Never move main directly from the updater.

The scheduled workflow performs steps 2-5 and opens a draft PR. It has no merge job. If repository settings prevent Actions from opening PRs, use the manual flow after the workflow pushes its branch.

## Promotion to trusted

Keep a new or materially changed skill experimental until all applicable automated tests pass and required manual acceptance evidence is recorded. Change trust_status to trusted in a reviewable commit only after the evidence exists.

## Rollback

Revert the sync PR that introduced the bad upstream commit. Do not edit the lock alone: the active skill, snapshot, manifests, registry, and lock must refer to the same commit.

