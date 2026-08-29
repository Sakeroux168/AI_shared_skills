# Evidence Method

Use this when a research request needs more than a quick factual lookup.

## Evidence hierarchy

Prefer evidence in roughly this order, while matching the source to the claim:

1. **Official / contractual** — specifications, official documentation, policy, release notes, product pages, legal or licensing records.
2. **Primary technical** — source code, commits, runtime reproduction, maintainer Issues/PRs/review threads, first-party artifacts.
3. **Independent technical analysis** — credible experts who show methods, data, or reproducible evidence.
4. **Community field reports** — Reddit, X/Twitter, Bilibili, Xiaohongshu, forums, comments, replies.
5. **Inference** — synthesis that should never be presented as if it were a sourced fact.

A lower-ranked source can be the best source for a user-experience claim. The hierarchy is about evidentiary weight for factual assertions, not about ignoring communities.

## Independence test

Before calling several sources a pattern, ask whether they are actually independent.

Do not double-count:
- reposts of the same post;
- articles that all quote one benchmark;
- comments repeating the parent post without new evidence;
- videos summarizing the same upstream announcement;
- multiple search results that resolve to the same original report.

Prefer distinct users, environments, dates, versions, and reproduction paths.

## Negative-evidence pass

For recommendation, adoption, architecture, tooling, or commercial decisions, deliberately search for evidence that could overturn the attractive story:

- regressions and unresolved bugs;
- incompatible versions or environments;
- rate limits, account bans, anti-bot/security restrictions;
- maintenance inactivity or abandoned dependencies;
- licensing, attribution, trademark, privacy, or commercial-use uncertainty;
- migration failures and rollback reports;
- performance or reliability failures under realistic conditions;
- credible maintainers saying a workflow is unsupported.

Record negative evidence even when the final recommendation remains positive.

## Comments and replies

Top-level posts often omit corrections, reproduction details, changed versions, or maintainer responses. Read comments/replies/nested threads when:

- the parent post makes a disputed technical claim;
- the decision depends on whether a failure was reproduced;
- a maintainer response may supersede the original claim;
- commenters provide version/environment details;
- sentiment is being inferred from a community discussion.

Do not expand every thread indiscriminately. Follow replies that can change the conclusion.

## Recency and version matching

For fast-changing software/platform behavior:

- record the version or commit when possible;
- prefer evidence that matches the user's current runtime;
- distinguish a historical bug from a current regression;
- do not let an old viral complaint outweigh a verified current fix;
- when current evidence is unavailable, state that the conclusion is time-bounded.

## Evidence saturation

Stop gathering when new independent sources no longer change any of:

- the decision;
- the dominant recurring pattern;
- a meaningful contradiction;
- the confidence level;
- an important failure mode or constraint.

More links are not automatically more confidence.

## Confidence

Use a simple conclusion-level label when it helps:

- **High** — strong primary evidence plus independent corroboration; no unresolved contradiction material to the decision.
- **Medium** — evidence is useful but missing a platform, current reproduction, or independent corroboration; or community reports materially disagree.
- **Low** — sparse, stale, indirect, or contradictory evidence; major required source unavailable.

Explain what would raise or lower confidence instead of using a numeric score with false precision.
