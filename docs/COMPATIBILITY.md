# Harness compatibility

Status meanings:

- verified: exercised in the named runtime or its documented filesystem contract, with evidence in this repository.
- theoretical: format/install path is supported, but the named runtime was not available for an end-to-end trigger test.
- incompatible: a known runtime requirement prevents use.
- unknown: the runtime's actual skill discovery contract has not been confirmed.

| Harness | Status | Verified scope | Remaining work |
|---|---|---|---|
| Codex | verified | SKILL.md structure validation, repository references, deterministic five-scenario acceptance, and isolated install copy | Verify the user's Windows Codex directory and automatic trigger behavior |
| Claude Code | theoretical | Upstream and local installers both support ~/.claude/skills; file copy is tested in isolation | Run Claude Code on the user's Windows machine and confirm discovery/triggering |
| Hermes | unknown | No path or parser assumption is encoded | Inspect the installed Hermes version and its real skill directory/manifest contract |
| DeepSeek Harness | unknown | Plain Markdown skill may be reusable | Inspect the installed DSH version, global skill search paths, and reload behavior |
| Generic .agents/skills | verified | Isolated copy to an explicit .agents/skills root and full file integrity | Confirm each consuming harness actually scans that shared root |

No harness is currently marked incompatible. Unknown must not be upgraded based only on a folder name or an upstream claim.

