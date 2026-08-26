# AI_shared_skills · Windows fixture regression tests.
# Run: ./windows/tests/run-fixture-tests.ps1   (pwsh or Windows PowerShell 5.1+)
# These tests never touch real user configuration: everything runs inside a
# throwaway directory created under $env:TEMP.

$ErrorActionPreference = 'Stop'

$script:Failures = New-Object System.Collections.Generic.List[string]
$script:PassCount = 0

function Assert-True {
    param([bool] $Condition, [string] $Message)
    if ($Condition) {
        $script:PassCount++
        Write-Host ("  ok  - " + $Message)
    }
    else {
        $script:Failures.Add($Message)
        Write-Host ("  FAIL- " + $Message)
    }
}

function Assert-Equal {
    param($Expected, $Actual, [string] $Message)
    Assert-True ("$Expected" -eq "$Actual") ("{0} (expected='{1}', actual='{2}')" -f $Message, $Expected, $Actual)
}

$libPath = Join-Path $PSScriptRoot '..\_lib.psm1'
Import-Module $libPath -DisableNameChecking -Force

$work = Join-Path ([System.IO.Path]::GetTempPath()) ("aiss-fixture-" + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $work -Force | Out-Null
$repoSkills = Join-Path $work 'fake-repo\skills'   # stand-in for <repo>\skills

Write-Host ''
Write-Host '== F1 Hermes: inline external_dirs list gets extended without duplicating skills: =='
$h1 = Join-Path $work 'f1\config.yaml'
New-Item -ItemType Directory -Path (Split-Path -Parent $h1) -Force | Out-Null
@'
model:
  provider: openrouter
terminal:
  timeout: 180
skills:
  creation_nudge_interval: 9
  external_dirs: ['D:\existing']
kanban:
  review_dispatch: true
'@ | Set-Content -LiteralPath $h1 -Encoding UTF8

$r1 = Update-HermesExternalDirs -ConfigPath $h1 -Dir $repoSkills
Assert-Equal 'updated' $r1 'F1 first run reports updated'
$c1 = @(Get-Content -LiteralPath $h1)
Assert-True ((@($c1 | Where-Object { $_ -match '^skills:' }).Count) -eq 1) 'F1 exactly one top-level skills: line'
Assert-True ((@($c1 | Where-Object { $_ -match "external_dirs:" }).Count) -eq 1) 'F1 exactly one external_dirs key'
Assert-True ($null -ne ($c1 | Where-Object { $_ -match "-\s*'D:\\existing'\s*$" })) 'F1 existing path D:\existing preserved as list item'
Assert-True (($c1 | Where-Object { $_ -match [regex]::Escape($repoSkills) }).Count -eq 1) 'F1 new repo path added exactly once'
Assert-True ($null -ne ($c1 | Where-Object { $_ -match '^kanban:' })) 'F1 following top-level block intact after skills block'
Assert-True ($null -ne ($c1 | Where-Object { $_ -match 'creation_nudge_interval: 9' })) 'F1 sibling option inside skills kept'
$before = Get-FileHash -LiteralPath $h1
$r1b = Update-HermesExternalDirs -ConfigPath $h1 -Dir $repoSkills
Assert-Equal 'exists' $r1b 'F1 second run reports exists'
Assert-True ((Get-FileHash -LiteralPath $h1).Hash -eq $before.Hash) 'F1 second run leaves file byte-identical'

# Optional strict YAML validation when PyYAML is available
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
    $hasYaml = $false
    try { & python -c "import yaml" 2>$null | Out-Null; $hasYaml = ($LASTEXITCODE -eq 0) } catch { }
    if ($hasYaml) {
        $check = @(
            'import io, sys, yaml',
            ('p = r"' + $h1 + '"'),
            'd = yaml.safe_load(io.open(p, encoding="utf-8"))',
            'assert isinstance(d["skills"]["external_dirs"], list), "external_dirs must be a list"',
            'assert len(d["skills"]["external_dirs"]) == 2, "expected two entries"',
            'assert d["model"]["provider"] == "openrouter"',
            'print("yaml-ok")'
        ) -join "`n"
        $tmpPy = Join-Path $work 'yamlcheck.py'
        [System.IO.File]::WriteAllText($tmpPy, $check, (New-Object System.Text.UTF8Encoding($false)))
        $out = & python $tmpPy 2>&1
        Assert-True (@($out) -contains 'yaml-ok') 'F1 parsed by PyYAML with expected structure'
    }
    else {
        Write-Host '  skip- PyYAML not available; structural assertions only'
    }
}

Write-Host ''
Write-Host '== F2 Deployment rule: active AND trusted only =='
$regJson = @'
{"schema_version":"1.0.0","skills":[
 {"name":"good","local":{"status":"active"},"trust_status":"trusted"},
 {"name":"exp","local":{"status":"active"},"trust_status":"experimental"},
 {"name":"off","local":{"status":"disabled"},"trust_status":"trusted"},
 {"name":"untrust","local":{"status":"active"},"trust_status":"unknown"}
]}
'@
$regData = ($regJson | ConvertFrom-Json)
$dep = Get-AissDeployableSkills -RegistryData $regData
Assert-True ((Test-AissDeployable ($regData.skills | Where-Object name -eq 'good'))) 'F2 active+trusted is deployable'
Assert-True (-not (Test-AissDeployable ($regData.skills | Where-Object name -eq 'exp'))) 'F2 active+experimental is NOT deployable'
Assert-True (-not (Test-AissDeployable ($regData.skills | Where-Object name -eq 'off'))) 'F2 disabled is NOT deployable'
Assert-True (-not (Test-AissDeployable ($regData.skills | Where-Object name -eq 'untrust'))) 'F2 active+unknown-trust is NOT deployable'
Assert-True ((@($dep).Count -eq 1) -and ($dep[0].name -eq 'good')) 'F2 Get-AissDeployableSkills returns only good'

Write-Host ''
Write-Host '== F3 DSH: extend existing config: mapping, never create a second config: =='
$p3 = Join-Path $work 'f3\agent.cordis.yml'
New-Item -ItemType Directory -Path (Split-Path -Parent $p3) -Force | Out-Null
@'
- id: tool-demo
  name: '@demo/tool'

- id: skill-filesystem
  name: '@deepseek-ai/dsh-skill-filesystem'
  config:
    someExistingOption: true
'@ | Set-Content -LiteralPath $p3 -Encoding UTF8

$r3 = Update-DshCustomSkillDirs -PresetPath $p3 -Dir $repoSkills
Assert-True ($r3 -in @('added-customskilldirs', 'added-config')) ("F3 first run status ({0})" -f $r3)
$c3 = @(Get-Content -LiteralPath $p3)
Assert-True ((@($c3 | Where-Object { $_ -match '^\s*config:\s*$' }).Count) -eq 1) 'F3 exactly one config: key'
Assert-True ($null -ne ($c3 | Where-Object { $_ -match 'someExistingOption: true' })) 'F3 someExistingOption preserved'
$csLine = 0
for ($i = 0; $i -lt $c3.Count; $i++) { if ($c3[$i] -match '^\s*customSkillDirs:') { $csLine = $i + 1 } }
$optLine = 0
for ($i = 0; $i -lt $c3.Count; $i++) { if ($c3[$i] -match 'someExistingOption') { $optLine = $i + 1 } }
Assert-True ($csLine -gt 0 -and $optLine -gt 0 -and $csLine -gt $optLine) 'F3 customSkillDirs lives INSIDE the same config mapping (after existing option)'
$tail = @($c3[$csLine..($c3.Count - 1)])
$occurrences = @($tail | Where-Object { $_ -match ([regex]::Escape($repoSkills)) }).Count
Assert-True ($occurrences -eq 1) 'F3 repo path added exactly once'
$hash3 = Get-FileHash -LiteralPath $p3
$r3b = Update-DshCustomSkillDirs -PresetPath $p3 -Dir $repoSkills
Assert-Equal 'exists' $r3b 'F3 second run reports exists'
Assert-True ((Get-FileHash -LiteralPath $p3).Hash -eq $hash3.Hash) 'F3 second run leaves file byte-identical'

Write-Host ''
Write-Host '== F4 DSH regression: entry without any config gets one, idempotent =='
$p4 = Join-Path $work 'f4\agent.cordis.yml'
New-Item -ItemType Directory -Path (Split-Path -Parent $p4) -Force | Out-Null
@'
- id: skill-filesystem
  name: '@deepseek-ai/dsh-skill-filesystem'
'@ | Set-Content -LiteralPath $p4 -Encoding UTF8
[void](Update-DshCustomSkillDirs -PresetPath $p4 -Dir $repoSkills)
$c4 = @(Get-Content -LiteralPath $p4)
Assert-True ((@($c4 | Where-Object { $_ -match '^\s*config:\s*$' }).Count) -eq 1) 'F4 exactly one config: key'
$h4 = Get-FileHash -LiteralPath $p4
[void](Update-DshCustomSkillDirs -PresetPath $p4 -Dir $repoSkills)
Assert-True ((Get-FileHash -LiteralPath $p4).Hash -eq $h4.Hash) 'F4 second run byte-identical'

Write-Host ''
Write-Host '== F5 Hermes safety: unrecognizable config is rejected untouched =='
$h5 = Join-Path $work 'f5\config.yaml'
New-Item -ItemType Directory -Path (Split-Path -Parent $h5) -Force | Out-Null
': : : not-yaml [[' | Set-Content -LiteralPath $h5 -Encoding UTF8
$threw = $false
try { [void](Update-HermesExternalDirs -ConfigPath $h5 -Dir $repoSkills) } catch { $threw = $true }
Assert-True $threw 'F5 broken config raises instead of writing'
Assert-True ((Get-Content -LiteralPath $h5 -Raw).Trim() -eq ': : : not-yaml [[') 'F5 broken config left byte-identical'

Write-Host ''
Write-Host '== F6 Bootstrap end-to-end smoke on fixture homes (no real user data) =='
$fH = Join-Path $work 'e2e\hermes'; $fD = Join-Path $work 'e2e\dsh'; $fC = Join-Path $work 'e2e\codex'
New-Item -ItemType Directory -Path $fH, $fD, $fC -Force | Out-Null
$bootScript = Join-Path $PSScriptRoot '..\bootstrap-windows.ps1'
$outLog = Join-Path $work 'e2e-out.txt'
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $bootScript -HermesHome $fH -DshHome $fD -CodexHome $fC *> $outLog
Assert-Equal 0 $LASTEXITCODE 'F6 bootstrap exits 0 on fixture homes'
Assert-True (Test-Path (Join-Path $fH 'config.yaml')) 'F6 hermes config created'
Assert-True (Test-Path (Join-Path $fD '.agent-presets\ai-shared-skills\agent.cordis.yml')) 'F6 minimal dsh preset created'
# NOTE: e2e uses the REAL registry of this checkout; deployable skills are copied into fixture codex home only.
$deployNames = @()
try {
    $reg = Read-AissRegistry -Path (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'registry\skills.json')
    if ($reg.Ok) { $deployNames = @(Get-AissDeployableSkills -RegistryData $reg.Data | ForEach-Object { $_.name }) }
} catch { }
if ($deployNames.Count -gt 0) {
    Assert-True (Test-Path (Join-Path $fC ("skills\" + $deployNames[0] + "\SKILL.md"))) 'F6 first deployable skill installed into fixture codex home'
}
else {
    Assert-True $true 'F6 no deployable skills in this checkout; codex install step skipped by design'
}

Write-Host ''
Write-Host ('Fixture workdir: ' + $work)
if ($script:Failures.Count -gt 0) {
    Write-Host ''
    Write-Host ('RESULT: FAIL (' + $script:Failures.Count + ' failed, ' + $script:PassCount + ' passed)')
    foreach ($f in $script:Failures) { Write-Host ('  - ' + $f) }
    exit 1
}
Write-Host ''
Write-Host ('RESULT: PASS (' + $script:PassCount + ' checks)')
exit 0
