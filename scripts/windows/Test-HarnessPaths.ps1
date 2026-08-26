$ErrorActionPreference = "Stop"

$candidates = @(
    @{ Harness = "Codex"; Path = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME "skills" } else { Join-Path $HOME ".codex\skills" } },
    @{ Harness = "Claude Code"; Path = if ($env:CLAUDE_HOME) { Join-Path $env:CLAUDE_HOME "skills" } else { Join-Path $HOME ".claude\skills" } },
    @{ Harness = "Generic .agents"; Path = if ($env:AGENTS_HOME) { Join-Path $env:AGENTS_HOME "skills" } else { Join-Path $HOME ".agents\skills" } },
    @{ Harness = "Hermes candidate only"; Path = "F:\Hermes\data\skills" },
    @{ Harness = "DeepSeek Harness candidate only"; Path = "D:\.dsh\skills" }
)

$candidates | ForEach-Object {
    [PSCustomObject]@{
        Harness = $_.Harness
        Path = $_.Path
        Exists = Test-Path -LiteralPath $_.Path
        SkillPresent = Test-Path -LiteralPath (Join-Path $_.Path "gpt-image-2-style-library\SKILL.md")
    }
} | Format-Table -AutoSize

Write-Host "Candidate paths are observations only. Confirm each harness version before installing or linking."

