# Maintenance

## Review-driven update

1. Start from the latest main and create sync/gpt-image-2-style-library-<short-sha>.
2. Run python scripts/check_upstream.py --json.
3. Run python scripts/sync_upstream.py --to-commit <full-sha> on the sync branch.
4. Confirm that every Skill affected by a changed upstream commit was automatically downgraded
   to experimental and has a pending trust_review record.
5. Inspect the curated snapshot, active Skill diff, rights metadata, attribution, upstream
   disclaimer, and generated report under reports/sync/.
6. Review knowledge-count deltas. A changed template/category/style/scene/case total is not by
   itself a validation failure; investigate the semantic diff and cross-reference integrity.
7. Run python scripts/validate_repository.py and python -m unittest discover -s tests -v.
8. Complete tests/manual-acceptance.md when the change affects matching, prompt structure, images, or harness behavior.
9. Commit only the listed integration paths, push the sync branch, and open a draft PR.
10. Review and merge manually. Never move main directly from the updater.

The scheduled workflow performs steps 2-5 and opens a draft PR. It has no merge job. If repository settings prevent Actions from opening PRs, use the manual flow after the workflow pushes its branch.

## Promotion to trusted

Keep a new Skill experimental until all applicable automated tests pass and required manual
acceptance evidence is recorded. A sync to a different upstream commit always returns every
affected Skill to experimental, even when automated tests pass in the sync branch.

Promote to trusted only with an explicit reviewed commit after the prescribed automated and manual
acceptance is complete. That promotion commit must update trust_status, replace pending evidence
with the new acceptance evidence, set trust_attestation.accepted_commit to the current locked
commit, set trust_attestation.skill_name to the exact Skill name, link a report that names both
that Skill and exact commit, and remove trust_review. The sync script never promotes a Skill.

## Registry growth

registry/skills.json may contain multiple Skills, including multiple Skills backed by one Source.
Names and Source IDs must be unique, each Skill must reference an existing Source, and each
Skill/Source/lock commit must agree. Add source-specific integrity validation when a new Source has
domain structures beyond the generic registry contract.

## Rights review

The upstream repository license and third-party content rights are separate records. Preserve the
upstream license and disclaimer, case-level source labels/URLs, and any source-specific license or
platform terms. Never relabel the whole prompt/image collection as MIT. Commercial reuse requires
case-by-case rights review and, where applicable, authorization from the original rights holder.

## Rollback

Revert the sync PR that introduced the bad upstream commit. Do not edit the lock alone: the active skill, snapshot, manifests, registry, and lock must refer to the same commit.
