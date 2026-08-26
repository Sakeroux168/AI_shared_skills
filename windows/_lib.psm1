# AI_shared_skills Windows one-click helpers (internal shared module).
# No machine-specific absolute paths may appear in this file.

Set-StrictMode -Version 2.0

$script:Utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$script:Utf8Bom = New-Object System.Text.UTF8Encoding($true)

function Get-AissContext {
    param(
        [Parameter(Mandatory)] [string] $WindowsDir
    )
    $root = Split-Path -Parent $WindowsDir
    $registryPath = Join-Path $root 'registry\skills.json'
    $skillsPath = Join-Path $root 'skills'
    $result = [ordered]@{
        Root = $root
        RegistryPath = $registryPath
        SkillsPath = $skillsPath
        Valid = $false
        Error = $null
    }
    if (-not (Test-Path -LiteralPath $registryPath -PathType Leaf)) {
        $result.Error = "找不到仓库清单文件 registry\skills.json（期望位置：$registryPath）"
        return [pscustomobject]$result
    }
    if (-not (Test-Path -LiteralPath $skillsPath -PathType Container)) {
        $result.Error = "找不到共享 Skill 目录 skills\（期望位置：$skillsPath）"
        return [pscustomobject]$result
    }
    $result.Valid = $true
    return [pscustomobject]$result
}

function Read-AissRegistry {
    param(
        [Parameter(Mandatory)] [string] $Path
    )
    try {
        $raw = [System.IO.File]::ReadAllText($Path)
        $data = $raw | ConvertFrom-Json
    }
    catch {
        return [pscustomobject]@{ Ok = $false; Data = $null; Error = "skills.json 不是有效的 JSON：$($_.Exception.Message)" }
    }
    if (-not $data.skills -or @($data.skills).Count -eq 0) {
        return [pscustomobject]@{ Ok = $false; Data = $null; Error = 'skills.json 中没有 skills 数组或数组为空' }
    }
    foreach ($skill in $data.skills) {
        foreach ($field in @('name', 'local', 'trust_status')) {
            if ($null -eq $skill.$field) {
                return [pscustomobject]@{ Ok = $false; Data = $null; Error = "skills.json 某条目缺少字段：$field" }
            }
        }
    }
    return [pscustomobject]@{ Ok = $true; Data = $data; Error = $null }
}

function Get-AissActiveSkills {
    param([Parameter(Mandatory)] $RegistryData)
    @($RegistryData.skills | Where-Object { $_.local.status -eq 'active' })
}

# Single deployment policy shared by bootstrap and doctor:
# a skill is auto-deployed only when local.status == 'active' AND trust_status == 'trusted'.
function Test-AissDeployable {
    param([Parameter(Mandatory)] $Skill)
    return ($null -ne $Skill.local -and $Skill.local.status -eq 'active' -and $Skill.trust_status -eq 'trusted')
}

function Get-AissDeployableSkills {
    param([Parameter(Mandatory)] $RegistryData)
    @($RegistryData.skills | Where-Object { Test-AissDeployable $_ })
}

function Get-NormalizedDir {
    param([AllowNull()][string] $Path)
    if ([string]::IsNullOrWhiteSpace($Path)) { return '' }
    $p = $Path.Trim().Trim('"').Trim("'")
    $p = $p -replace '/', '\'
    $p = $p.TrimEnd('\')
    return $p.ToLowerInvariant()
}

function ConvertTo-YamlSingleQuoted {
    param([Parameter(Mandatory)][string] $Value)
    return "'" + $Value.Replace("'", "''") + "'"
}

function Get-AissStateDir {
    if (-not [string]::IsNullOrWhiteSpace($env:AISS_STATE_DIR)) { return $env:AISS_STATE_DIR }
    $base = Join-Path $env:LOCALAPPDATA 'AI_shared_skills'
    if (-not (Test-Path -LiteralPath $base)) {
        New-Item -ItemType Directory -Path $base -Force | Out-Null
    }
    return $base
}

function New-AissBackup {
    param(
        [Parameter(Mandatory)] [string] $Path,
        [Parameter(Mandatory)] [string] $Component
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $dir = Join-Path (Get-AissStateDir) "backups\$stamp\$Component"
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $dest = Join-Path $dir (Split-Path -Leaf $Path)
    Copy-Item -LiteralPath $Path -Destination $dest -Force
    return $dest
}

function Write-TextAtomic {
    param(
        [Parameter(Mandatory)] [string] $Path,
        [Parameter(Mandatory)] [string] $Text
    )
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $tmp = Join-Path $dir ("{0}.aiss-tmp-{1}" -f (Split-Path -Leaf $Path), [guid]::NewGuid().ToString('N').Substring(0, 8))
    [System.IO.File]::WriteAllText($tmp, $Text, $script:Utf8NoBom)
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}

function Read-TextAuto {
    param([Parameter(Mandatory)] [string] $Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $sr = New-Object System.IO.StreamReader($Path, $true)
    try { return $sr.ReadToEnd() } finally { $sr.Close() }
}

# ---------------- Hermes ----------------

function Get-HermesInfo {
    param([string] $OverrideHome)
    $info = [ordered]@{ Installed = $false; Home = $null; ConfigPath = $null; Source = '' }
    if (-not [string]::IsNullOrWhiteSpace($OverrideHome)) {
        $info.Home = $OverrideHome
        $info.Source = '参数指定'
        $info.Installed = Test-Path -LiteralPath $OverrideHome
    }
    else {
        $envHome = $env:HERMES_HOME
        if (-not [string]::IsNullOrWhiteSpace($envHome)) {
            $info.Home = $envHome
            $info.Source = 'HERMES_HOME 环境变量'
            $info.Installed = $true
        }
        else {
            $fallback = Join-Path $env:LOCALAPPDATA 'hermes'
            $cmd = Get-Command hermes.exe -ErrorAction SilentlyContinue
            if (-not $cmd) { $cmd = Get-Command hermes -ErrorAction SilentlyContinue }
            if (Test-Path -LiteralPath $fallback) {
                $info.Home = $fallback
                $info.Source = '默认位置 %LOCALAPPDATA%\hermes'
                $info.Installed = $true
            }
            elseif ($cmd) {
                $info.Home = $fallback
                $info.Source = '检测到 hermes 命令，使用默认 home'
                $info.Installed = $true
            }
        }
    }
    if ($info.Home) { $info.ConfigPath = Join-Path $info.Home 'config.yaml' }
    return [pscustomobject]$info
}

function Test-HermesConfigListsDir {
    param(
        [Parameter(Mandatory)] [string] $ConfigText,
        [Parameter(Mandatory)] [string] $NormalizedDir
    )
    $lines = $ConfigText -split "`r?`n"
    $inSkills = $false
    $inExt = $false
    $extIndent = ''
    foreach ($line in $lines) {
        if ($line -match '^[A-Za-z_][A-Za-z0-9_.-]*:\s*(?:#.*)?$') {
            if ($line -match '^skills:\s*(?:#.*)?$') { $inSkills = $true; $inExt = $false; continue }
            if ($inSkills) { $inSkills = $false; $inExt = $false }
            continue
        }
        if (-not $inSkills) { continue }
        if ($line -match '^(\s+)external_dirs:\s*(\S.*)?$') {
            $extIndent = $Matches[1]
            if ($Matches[2]) {
                $inline = $Matches[2].Trim()
                if ($inline.StartsWith('[') -and $inline.EndsWith(']')) {
                    foreach ($seg in $inline.Trim('[', ']').Split(',')) {
                        $v = $seg.Trim().Trim('"').Trim("'")
                        if ((Get-NormalizedDir $v) -eq $NormalizedDir) { return $true }
                    }
                }
                continue
            }
            $inExt = $true
            continue
        }
        if ($inExt) {
            if ($line -match '^\s*-\s+(.+)$') {
                $val = $Matches[1].Trim()
                if ((Get-NormalizedDir $val) -eq $NormalizedDir) { return $true }
            }
            elseif ($line.Trim() -ne '') { $inExt = $false }
        }
    }
    return $false
}

function Update-HermesExternalDirs {
    param(
        [Parameter(Mandatory)] [string] $ConfigPath,
        [Parameter(Mandatory)] [string] $Dir
    )
    $quoted = ConvertTo-YamlSingleQuoted $Dir
    if (-not (Test-Path -LiteralPath $ConfigPath)) {
        $text = "# Created by AI_shared_skills one-click bootstrap`nskills:`n  external_dirs:`n    - $quoted`n"
        Write-TextAtomic -Path $ConfigPath -Text $text
        return 'created'
    }
    $text = Read-TextAuto $ConfigPath
    $lines0 = @($text -split "`r?`n")
    $looksYaml = @($lines0 | Where-Object { $_ -match '^[A-Za-z_][A-Za-z0-9_.-]*:\s*(?:#.*)?$' }).Count -gt 0
    if (-not $looksYaml) {
        throw "现有 config.yaml 无法识别（不是有效的 YAML 配置），已保持原样未修改"
    }
    if (Test-HermesConfigListsDir -ConfigText $text -NormalizedDir (Get-NormalizedDir $Dir)) {
        return 'exists'
    }
    $nl = if ($text -contains "`r`n") { "`r`n" } else { "`n" }
    $lines = @($text -split "`r?`n")

    # locate the FIRST top-level skills: block
    $skillsIdx = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^skills:\s*(?:#.*)?$') { $skillsIdx = $i; break }
    }

    if ($skillsIdx -ge 0) {
        $end = $lines.Count
        for ($j = $skillsIdx + 1; $j -lt $lines.Count; $j++) {
            if ($lines[$j] -match '^[A-Za-z_][A-Za-z0-9_.-]*:\s*(?:#.*)?$') { $end = $j; break }
        }

        # locate external_dirs inside the skills block
        $extIdx = -1
        $extIndentLen = 0
        $inlineRest = ''
        for ($j = $skillsIdx + 1; $j -lt $end; $j++) {
            if ($lines[$j] -match '^(\s+)external_dirs:\s*(.*)$') {
                $extIdx = $j
                $extIndentLen = $Matches[1].Length
                $inlineRest = $Matches[2].Trim()
                break
            }
        }

        $block = New-Object System.Collections.Generic.List[string]
        [void]$block.Add($lines[$skillsIdx])

        if ($extIdx -ge 0) {
            # children before external_dirs stay in place
            for ($k = $skillsIdx + 1; $k -lt $extIdx; $k++) { [void]$block.Add($lines[$k]) }

            # gather existing dir values
            $oldValues = New-Object System.Collections.Generic.List[string]
            $stop = $extIdx + 1
            if ($inlineRest.StartsWith('[') -and $inlineRest.EndsWith(']')) {
                foreach ($seg in $inlineRest.Trim('[', ']').Split(',')) {
                    $v = $seg.Trim()
                    if ($v) { [void]$oldValues.Add($v) }
                }
                $stop = $extIdx + 1
            }
            else {
                $k = $extIdx + 1
                while ($k -lt $end) {
                    $l = $lines[$k]
                    if ($l.Trim() -eq '') { $k++; continue }
                    if ($l -match '^(\s*)-\s+(.+)$' -and $Matches[1].Length -gt $extIndentLen) {
                        [void]$oldValues.Add($Matches[2].Trim())
                        $k++
                    }
                    else { break }
                }
                $stop = $k
            }

            [void]$block.Add((' ' * $extIndentLen) + 'external_dirs:')
            foreach ($v in $oldValues) { [void]$block.Add("    - $v") }
            [void]$block.Add(("    - {0}" -f $quoted))

            # children after the external_dirs list stay in place
            for ($k = $stop; $k -lt $end; $k++) { [void]$block.Add($lines[$k]) }
        }
        else {
            [void]$block.Add('  external_dirs:')
            [void]$block.Add(("    - {0}" -f $quoted))
            for ($k = $skillsIdx + 1; $k -lt $end; $k++) { [void]$block.Add($lines[$k]) }
        }

        $out = New-Object System.Collections.Generic.List[string]
        for ($k = 0; $k -lt $skillsIdx; $k++) { [void]$out.Add($lines[$k]) }
        foreach ($b in $block) { [void]$out.Add($b) }
        for ($k = $end; $k -lt $lines.Count; $k++) { [void]$out.Add($lines[$k]) }
        Write-TextAtomic -Path $ConfigPath -Text (($out -join $nl) + $nl)
        return 'updated'
    }

    # no skills: block anywhere — append one
    $out2 = New-Object System.Collections.Generic.List[string]
    foreach ($l in $lines) { [void]$out2.Add($l) }
    while ($out2.Count -gt 0 -and $out2[$out2.Count - 1].Trim() -eq '') { $out2.RemoveAt($out2.Count - 1) }
    [void]$out2.Add('skills:')
    [void]$out2.Add('  external_dirs:')
    [void]$out2.Add(("    - {0}" -f $quoted))
    Write-TextAtomic -Path $ConfigPath -Text (($out2 -join $nl) + $nl)
    return 'updated'
}

# ---------------- DeepSeek Harness ----------------

function Get-DshInfo {
    param([string] $OverrideHome)
    $info = [ordered]@{ Installed = $false; Home = $null; SettingsPath = $null; PresetName = $null; PresetPath = $null; Source = '' }
    if (-not [string]::IsNullOrWhiteSpace($OverrideHome)) {
        $info.Home = $OverrideHome
        $info.Source = '参数指定'
        $info.Installed = Test-Path -LiteralPath $OverrideHome
    }
    else {
        $envHome = $env:DSH_HOME
        if (-not [string]::IsNullOrWhiteSpace($envHome)) {
            $info.Home = $envHome
            $info.Source = 'DSH_HOME 环境变量'
            $info.Installed = $true
        }
        else {
            $fallback = Join-Path $env:USERPROFILE '.dsh'
            $cmd = Get-Command dsh -ErrorAction SilentlyContinue
            if (Test-Path -LiteralPath $fallback) {
                $info.Home = $fallback
                $info.Source = '默认位置 ~/.dsh'
                $info.Installed = $true
            }
            elseif ($cmd) {
                $info.Home = $fallback
                $info.Source = '检测到 dsh 命令，使用默认 home'
                $info.Installed = $true
            }
        }
    }
    if ($info.Home) {
        $info.SettingsPath = Join-Path $info.Home 'settings.yaml'
        $presetName = $null
        $settingsText = Read-TextAuto $info.SettingsPath
        if ($settingsText) {
            $block = [regex]::Match($settingsText, '(?ms)^agent-presets:\r?\n(?:(?!^[A-Za-z_#]).)*')
            if ($block.Success -and $block.Value -match '(?m)^\s+default:\s*([A-Za-z0-9_-]+)\s*$') {
                $presetName = $Matches[1]
            }
        }
        if ($presetName) {
            $info.PresetName = $presetName
            $info.PresetPath = Join-Path $info.Home (".agent-presets\$presetName\agent.cordis.yml")
        }
    }
    return [pscustomobject]$info
}

function Get-DshRuntimeStability {
    param([Parameter(Mandatory)] [pscustomobject] $DshInfo)
    $res = [ordered]@{ Stable = $true; Reasons = @(); Version = $null; Command = $null }
    $cmd = Get-Command dsh -ErrorAction SilentlyContinue
    if ($cmd) {
        $res.Command = $cmd.Source
        if ($cmd.Source -match '_npx') {
            $res.Stable = $false
            $res.Reasons += "PATH 中的 dsh 来自 npx 缓存（$($cmd.Source)），缓存清理后会失效"
        }
    }
    $nm = Join-Path $DshInfo.Home 'profiles\node_modules'
    if (Test-Path -LiteralPath $nm) {
        $bad = @(Get-ChildItem -LiteralPath $nm -Recurse -Directory -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.LinkType -and (($_.Target -join '') -match '_npx') })
        if ($bad.Count -gt 0) {
            $res.Stable = $false
            $res.Reasons += ("DSH profile 运行时仍有 {0} 个链接指向 npx 缓存目录" -f $bad.Count)
        }
    }
    if ($cmd) {
        try {
            $v = & $cmd.Source --version 2>$null
            if ($LASTEXITCODE -eq 0) { $res.Version = (@($v) | Select-Object -First 1) }
        } catch { }
    }
    return [pscustomobject]$res
}

function New-MinimalDshPreset {
    param(
        [Parameter(Mandatory)] [string] $Home,
        [Parameter(Mandatory)] [string] $Dir
    )
    $presetId = 'ai-shared-skills'
    $presetDir = Join-Path $Home ".agent-presets\$presetId"
    New-Item -ItemType Directory -Path $presetDir -Force | Out-Null
    $presetPath = Join-Path $presetDir 'agent.cordis.yml'
    $quoted = ConvertTo-YamlSingleQuoted $Dir
    $text = "# Created by AI_shared_skills one-click bootstrap (minimal preset)`n- id: skill-filesystem`n  name: '@deepseek-ai/dsh-skill-filesystem'`n  config:`n    customSkillDirs:`n      - $quoted`n"
    Write-TextAtomic -Path $presetPath -Text $text
    $settingsPath = Join-Path $Home 'settings.yaml'
    $settingsText = Read-TextAuto $settingsPath
    if ($null -eq $settingsText) {
        Write-TextAtomic -Path $settingsPath -Text "agent-presets:`n  default: $presetId`n"
    }
    elseif ($settingsText -notmatch '(?m)^agent-presets:') {
        $settingsText = $settingsText.TrimEnd() + "`n`nagent-presets:`n  default: $presetId`n"
        Write-TextAtomic -Path $settingsPath -Text $settingsText
    }
    elseif ($settingsText) {
        # agent-presets section exists but has no default: insert one right after the key line
        $hasBlock = [regex]::Match($settingsText, '(?ms)^agent-presets:\r?\n(?:(?!^[A-Za-z_#]).)*')
        if (-not ($hasBlock.Success -and $hasBlock.Value -match '(?m)^\s+default:\s*[A-Za-z0-9_-]+\s*$')) {
            $settingsText = [regex]::Replace($settingsText, '(?m)^(agent-presets:\s*)$', "`$1`n  default: $presetId")
            Write-TextAtomic -Path $settingsPath -Text $settingsText
        }
    }
    return $presetPath
}

function Update-DshCustomSkillDirs {
    param(
        [Parameter(Mandatory)] [string] $PresetPath,
        [Parameter(Mandatory)] [string] $Dir
    )
    $text = Read-TextAuto $PresetPath
    if ($null -eq $text) { throw "预设文件不存在：$PresetPath" }
    $norm = Get-NormalizedDir $Dir
    $nl = if ($text -contains "`r`n") { "`r`n" } else { "`n" }
    $lines = $text -split "`r?`n"
    $entryStart = -1
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match '^-\s+id:\s*skill-filesystem\s*$') { $entryStart = $i; break }
    }
    if ($entryStart -lt 0) {
        $quoted = ConvertTo-YamlSingleQuoted $Dir
        $append = @('- id: skill-filesystem', "  name: '@deepseek-ai/dsh-skill-filesystem'", '  config:', '    customSkillDirs:', "      - $quoted")
        $newText = $text.TrimEnd() + $nl + $nl + ($append -join $nl) + $nl
        Write-TextAtomic -Path $PresetPath -Text $newText
        return 'appended-entry'
    }
    $entryEnd = $lines.Count
    for ($j = $entryStart + 1; $j -lt $lines.Count; $j++) {
        if ($lines[$j] -match '^-\s+id:') { $entryEnd = $j; break }
    }
    $csIdx = -1
    $csIndent = ''
    $lastItem = -1
    for ($j = $entryStart; $j -lt $entryEnd; $j++) {
        if ($lines[$j] -match '^(\s+)customSkillDirs:\s*$') { $csIdx = $j; $csIndent = $Matches[1] }
        if ($csIdx -ge 0 -and $j -gt $csIdx) {
            if ($lines[$j] -match '^(\s*)-\s+(.+)$' -and $Matches[1].Length -gt $csIndent.Length) {
                $val = $Matches[2].Trim()
                if ((Get-NormalizedDir $val) -eq $norm) { return 'exists' }
                $lastItem = $j
            }
            elseif ($lines[$j].Trim() -ne '' -and $lines[$j] -notmatch '^\s') { break }
        }
    }
    $quoted = ConvertTo-YamlSingleQuoted $Dir
    $itemIndent = ' ' * ($csIndent.Length + 2)
    if ($csIdx -ge 0) {
        $at = if ($lastItem -gt $csIdx) { $lastItem } else { $csIdx }
        $out = New-Object System.Collections.Generic.List[string]
        for ($k = 0; $k -le $at; $k++) { [void]$out.Add($lines[$k]) }
        [void]$out.Add("$itemIndent- $quoted")
        for ($k = $at + 1; $k -lt $lines.Count; $k++) { [void]$out.Add($lines[$k]) }
        $tail = ''
        if (-not $text.EndsWith("`n")) { $tail = $nl }
        Write-TextAtomic -Path $PresetPath -Text (($out -join $nl) + $tail)
        return 'updated'
    }
    # no customSkillDirs yet — if a config: mapping already exists, extend it in place
    $cfgIdx = -1
    $cfgIndentLen = 0
    for ($j = $entryStart; $j -lt $entryEnd; $j++) {
        if ($lines[$j] -match '^(\s+)config:\s*$') { $cfgIdx = $j; $cfgIndentLen = $Matches[1].Length; break }
    }
    if ($cfgIdx -ge 0) {
        # find the end of the config mapping: first non-blank line indented <= the config key
        $cfgEnd = $entryEnd
        for ($k = $cfgIdx + 1; $k -lt $entryEnd; $k++) {
            if ($lines[$k].Trim() -eq '') { continue }
            $ind = ($lines[$k] -replace '^(\s*).*', '$1').Length
            if ($ind -le $cfgIndentLen) { $cfgEnd = $k; break }
        }
        # anchor on the last non-blank line of the mapping so existing options stay first
        $anchor = $cfgIdx
        for ($k = $cfgEnd - 1; $k -gt $cfgIdx; $k--) {
            if ($lines[$k].Trim() -ne '') { $anchor = $k; break }
        }
        $b1 = (' ' * $cfgIndentLen) + '  '
        $b2 = (' ' * $cfgIndentLen) + '    '
        $out = New-Object System.Collections.Generic.List[string]
        for ($k = 0; $k -le $anchor; $k++) { [void]$out.Add($lines[$k]) }
        [void]$out.Add("${b1}customSkillDirs:")
        [void]$out.Add("$b2- $quoted")
        for ($k = $anchor + 1; $k -lt $lines.Count; $k++) { [void]$out.Add($lines[$k]) }
        Write-TextAtomic -Path $PresetPath -Text (($out -join $nl) + $nl)
        return 'added-customskilldirs'
    }

    # no config at all: create one right after this entry's name line
    $nameIdx = -1
    for ($j = $entryStart + 1; $j -lt $entryEnd; $j++) {
        if ($lines[$j] -match '^\s+name:\s*.+\s*$') { $nameIdx = $j; break }
    }
    if ($nameIdx -lt 0) { $nameIdx = $entryStart }
    $baseIndent = $lines[$nameIdx] -replace '^(\s*).*', '$1'
    $b0 = $baseIndent
    $b1 = $baseIndent + '  '
    $b2 = $baseIndent + '    '
    $block = @("${b0}config:", "${b1}customSkillDirs:", "$b2- $quoted")
    $out = New-Object System.Collections.Generic.List[string]
    for ($k = 0; $k -le $nameIdx; $k++) { [void]$out.Add($lines[$k]) }
    foreach ($b in $block) { [void]$out.Add($b) }
    for ($k = $nameIdx + 1; $k -lt $lines.Count; $k++) { [void]$out.Add($lines[$k]) }
    Write-TextAtomic -Path $PresetPath -Text (($out -join $nl) + $nl)
    return 'added-config'
}

# ---------------- Codex ----------------

function Test-DshPresetListsDir {
    param(
        [Parameter(Mandatory)] [string] $PresetText,
        [Parameter(Mandatory)] [string] $NormalizedDir
    )
    $lines = $PresetText -split "`r?`n"
    $csIdx = -1; $csIndent = ''
    foreach ($line in $lines) {
        if ($line -match '^(\s*)-\s+id:\s*skill-filesystem\s*$') { $csIdx = -1; $csIndent = ''; continue }
        if ($line -match '^(\s+)customSkillDirs:\s*$') { $csIdx = 1; $csIndent = $Matches[1]; continue }
        if ($csIndent -ne '' -and $line -match '^(\s*)-\s+(.+)$' -and $Matches[1].Length -gt $csIndent.Length) {
            if ((Get-NormalizedDir ($Matches[2].Trim())) -eq $NormalizedDir) { return $true }
        }
        elseif ($csIndent -ne '' -and $line -match '^[A-Za-z_#]' ) { $csIndent = '' }
    }
    return $false
}

function Get-CodexInfo {
    param([string] $OverrideHome)
    $info = [ordered]@{ Installed = $false; Home = $null; SkillsDir = $null; Source = '' }
    if (-not [string]::IsNullOrWhiteSpace($OverrideHome)) {
        $info.Home = $OverrideHome
        $info.Source = '参数指定'
        $info.Installed = Test-Path -LiteralPath $OverrideHome
    }
    else {
        $envHome = $env:CODEX_HOME
        $cmd = Get-Command codex -ErrorAction SilentlyContinue
        if (-not [string]::IsNullOrWhiteSpace($envHome)) {
            $info.Home = $envHome
            $info.Source = 'CODEX_HOME 环境变量'
            $info.Installed = $true
        }
        elseif (Test-Path -LiteralPath (Join-Path $env:USERPROFILE '.codex')) {
            $info.Home = Join-Path $env:USERPROFILE '.codex'
            $info.Source = '默认位置 ~/.codex'
            $info.Installed = $true
        }
        elseif ($cmd) {
            $info.Home = Join-Path $env:USERPROFILE '.codex'
            $info.Source = '检测到 codex 命令，使用默认 home'
            $info.Installed = $true
        }
    }
    if ($info.Home) { $info.SkillsDir = Join-Path $info.Home 'skills' }
    return [pscustomobject]$info
}

function Get-TreeFingerprint {
    param([Parameter(Mandatory)] [string] $Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $map = @{}
    Get-ChildItem -LiteralPath $Path -Recurse -File -Force | ForEach-Object {
        $rel = $_.FullName.Substring($Path.Length).TrimStart('\').ToLowerInvariant()
        $map[$rel] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }
    return $map
}

function Copy-Tree {
    param(
        [Parameter(Mandatory)] [string] $Source,
        [Parameter(Mandatory)] [string] $Dest
    )
    New-Item -ItemType Directory -Path (Split-Path -Parent $Dest) -Force | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Dest -Recurse -Force
}

function Sync-CodexSkill {
    param(
        [Parameter(Mandatory)] [string] $SourceDir,
        [Parameter(Mandatory)] [string] $SkillsRoot,
        [Parameter(Mandatory)] [string] $Name
    )
    $dest = Join-Path $SkillsRoot $Name
    if (-not (Test-Path -LiteralPath $SkillsRoot)) {
        New-Item -ItemType Directory -Path $SkillsRoot -Force | Out-Null
    }
    if (-not (Test-Path -LiteralPath $dest)) {
        Copy-Tree -Source $SourceDir -Dest $dest
        return 'installed'
    }
    $srcFp = Get-TreeFingerprint $SourceDir
    $dstFp = Get-TreeFingerprint $dest
    $srcKeys = @($srcFp.Keys)
    $dstKeys = @($dstFp.Keys)
    $same = ($srcKeys.Count -eq $dstKeys.Count) -and (-not (Compare-Object $srcKeys $dstKeys)) -and (@($srcKeys | Where-Object { $srcFp[$_] -ne $dstFp[$_] }).Count -eq 0)
    if ($same) { return 'identical' }
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $backupDir = Join-Path (Get-AissStateDir) "backups\$stamp\Codex"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Move-Item -LiteralPath $dest -Destination (Join-Path $backupDir $Name) -Force
    Copy-Tree -Source $SourceDir -Dest $dest
    return 'refreshed'
}

# ---------------- output helpers ----------------

function Format-StatusLine {
    param(
        [Parameter(Mandatory)][string] $Name,
        [Parameter(Mandatory)][ValidateSet('PASS','WARN','FAIL','SKIP')][string] $Status,
        [string] $Note = ''
    )
    $line = "{0} [{1}]" -f $Name, $Status
    if ($Note) { $line += " — $Note" }
    return $line
}

function Write-AissBanner {
    param([Parameter(Mandatory)][string[]] $Steps)
    Write-Host ''
    Write-Host '=== AI_shared_skills Windows 工具 ==='
    Write-Host '本次将依次检查：'
    foreach ($s in $steps) { Write-Host ("  · " + $s) }
    Write-Host ''
}

function Write-Step {
    param([string] $Text)
    Write-Host ''
    Write-Host ("▶ " + $Text)
}
