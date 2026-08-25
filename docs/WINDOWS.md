# Windows follow-up

Run these checks on the user's Windows machine after the GitHub PR is merged.

## 1. Clone and validate

    git clone https://github.com/Sakeroux168/AI_shared_skills.git
    Set-Location AI_shared_skills
    python scripts/validate_repository.py
    python -m unittest discover -s tests -v

## 2. Discover real harness paths

    powershell -ExecutionPolicy Bypass -File scripts/windows/Test-HarnessPaths.ps1

Record actual versions and discovered directories. Do not create junctions or symlinks yet.

## 3. Test copy-based installs first

    python scripts/install_skill.py gpt-image-2-style-library --target codex
    python scripts/install_skill.py gpt-image-2-style-library --target claude-code
    python scripts/install_skill.py gpt-image-2-style-library --target agents

For Hermes and DeepSeek Harness, use --target-root <verified-skill-root> only after their actual discovery contract is known.

## 4. End-to-end acceptance

Start a fresh session in each harness, explicitly invoke gpt-image-2-style-library, and run the five prompts in tests/fixtures/prompt_cases.json. Record whether the skill triggers, reads the compact reference, reaches the full source knowledge, and returns the required six prompt blocks.

## 5. Decide shared-directory strategy

Use copy-based installs as the safe baseline. Consider a junction or symlink only after every harness's update/reload behavior is verified and the target is an explicit skill directory, never a broad user or workspace directory.

