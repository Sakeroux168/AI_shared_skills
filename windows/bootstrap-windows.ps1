# AI_shared_skills 一键配置（Windows）
# 用法：双击 windows\一键配置.cmd，或在 PowerShell 中运行本脚本。
# 本脚本自动定位仓库根目录，不依赖任何固定盘符或用户名。

param(
    [string] $HermesHome,
    [string] $DshHome,
    [string] $CodexHome
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

Import-Module (Join-Path $PSScriptRoot '_lib.psm1') -DisableNameChecking

$script:ComponentStatus = [ordered]@{
    'AI_shared_skills Registry' = 'SKIP'
    'Codex'                     = 'SKIP'
    'Hermes'                    = 'SKIP'
    'DeepSeek Harness'          = 'SKIP'
}
$script:Details = New-Object System.Collections.Generic.List[string]
$script:Hints = New-Object System.Collections.Generic.List[string]

function Set-ComponentStatus {
    param([string] $Name, [string] $Status, [string] $Note = '')
    $order = @('SKIP', 'PASS', 'WARN', 'FAIL')
    $old = $script:ComponentStatus[$Name]
    if ($order.IndexOf($Status) -gt $order.IndexOf($old)) { $script:ComponentStatus[$Name] = $Status }
    $line = Format-StatusLine -Name $Name -Status $Status -Note $Note
    if ($Status -ne 'PASS' -or $Note) { $script:Details.Add($line) }
}

function Write-Step {
    param([string] $Text)
    Write-Host ''
    Write-Host ("▶ " + $Text)
}

Write-AissBanner -Steps @(
    '仓库与 Registry 校验',
    '检测已安装的 Harness（Codex / Hermes / DeepSeek Harness）',
    '配置 Hermes 直接读取本仓库 skills',
    '配置 DeepSeek Harness 直接读取本仓库 skills',
    '把 Registry 中启用的 Skill 安装/刷新到 Codex'
)

$repoSkills = $null

# ---------- 1. 仓库与 Registry ----------
Write-Step '[1/5] 校验仓库与 Registry'
try {
    $ctx = Get-AissContext -WindowsDir $PSScriptRoot
    if (-not $ctx.Valid) { throw $ctx.Error }
    $reg = Read-AissRegistry -Path $ctx.RegistryPath
    if (-not $reg.Ok) { throw $reg.Error }
    $active = Get-AissActiveSkills -RegistryData $reg.Data
    $repoSkills = $ctx.SkillsPath
    $script:ComponentStatus['AI_shared_skills Registry'] = 'PASS'
    Write-Host ("  仓库：" + $ctx.Root)
    Write-Host ("  Registry 有效，启用中的专业 Skill：" + (@($active).Count) + " 个")
}
catch {
    Write-Host ("  错误：" + $_.Exception.Message)
    Set-ComponentStatus -Name 'AI_shared_skills Registry' -Status 'FAIL' -Note $_.Exception.Message
    $script:Hints.Add('仓库或 registry/skills.json 损坏：请重新从 GitHub 下载 AI_shared_skills 后再运行。')
}

$canContinue = ($script:ComponentStatus['AI_shared_skills Registry'] -eq 'PASS')

# ---------- 2-5 各 Harness ----------
if ($canContinue) {
    # ----- Hermes -----
    Write-Step '[3/5] 配置 Hermes（direct-read）'
    try {
        $hermes = Get-HermesInfo -OverrideHome $HermesHome
        if (-not $hermes.Installed) {
            Write-Host '  未检测到已安装的 Hermes，跳过。'
            Set-ComponentStatus -Name 'Hermes' -Status 'SKIP' -Note '未检测到安装'
        }
        else {
            Write-Host ("  Hermes home：{0}（{1}）" -f $hermes.Home, $hermes.Source)
            $existing = Read-TextAuto $hermes.ConfigPath
            if ($existing -and (Test-HermesConfigListsDir -ConfigText $existing -NormalizedDir (Get-NormalizedDir $repoSkills))) {
                Write-Host '  external_dirs 已指向本仓库，无需修改。'
                Set-ComponentStatus 'Hermes' 'PASS' '已是最新'
            }
            else {
                $backup = New-AissBackup -Path $hermes.ConfigPath -Component 'Hermes'
                if ($backup) { $script:Details.Add(("  已备份原配置 → {0}" -f $backup)) }
                $res = Update-HermesExternalDirs -ConfigPath $hermes.ConfigPath -Dir $repoSkills
                switch ($res) {
                    'created' { Write-Host '  已创建 config.yaml 并写入 external_dirs。'; Set-ComponentStatus 'Hermes' 'PASS' '已创建配置' }
                    'updated' { Write-Host '  已在现有 config.yaml 中追加 external_dirs（其他字段未改动）。'; Set-ComponentStatus 'Hermes' 'PASS' '已更新' }
                    default   { Write-Host '  external_dirs 已指向本仓库。'; Set-ComponentStatus 'Hermes' 'PASS' '已是最新' }
                }
            }
        }
    }
    catch {
        Set-ComponentStatus 'Hermes' 'FAIL' $_.Exception.Message
        $script:Hints.Add("Hermes 配置失败：可手动在 Hermes 的 config.yaml 的 skills: 下添加 external_dirs: 指向 $repoSkills")
    }

    # ----- DeepSeek Harness -----
    Write-Step '[4/5] 配置 DeepSeek Harness（direct-read）'
    try {
        $dsh = Get-DshInfo -OverrideHome $DshHome
        if (-not $dsh.Installed) {
            Write-Host '  未检测到已安装的 DeepSeek Harness，跳过。'
            Set-ComponentStatus -Name 'DeepSeek Harness' -Status 'SKIP' -Note '未检测到安装'
        }
        else {
            Write-Host ("  DSH home：{0}（{1}）" -f $dsh.Home, $dsh.Source)
            $stab = Get-DshRuntimeStability -DshInfo $dsh
            if ($stab.Version) { Write-Host ("  运行时版本：" + $stab.Version) }
            if (-not $stab.Stable) {
                foreach ($r in $stab.Reasons) {
                    Set-ComponentStatus -Name 'DeepSeek Harness' -Status 'WARN' -Note $r
                    $script:Hints.Add("DSH 运行时依赖 npx 缓存，缓存清理后会失效。修复方式：npm install -g @deepseek-ai/dsh@当前版本，然后正常启动一次 dsh 即可自动迁移。详见仓库报告或 doctor 提示。")
                }
            }
            if ($dsh.PresetName -and (Test-Path -LiteralPath $dsh.PresetPath)) {
                $ptext = Read-TextAuto $dsh.PresetPath
                if ($ptext -and (Test-DshPresetListsDir -PresetText $ptext -NormalizedDir (Get-NormalizedDir $repoSkills))) {
                    Write-Host '  customSkillDirs 已包含本仓库，无需修改。'
                    Set-ComponentStatus 'DeepSeek Harness' 'PASS' '已是最新'
                }
                else {
                    $backup = New-AissBackup -Path $dsh.PresetPath -Component 'DSH-preset'
                    if ($backup) { $script:Details.Add(("  已备份预设 → {0}" -f $backup)) }
                    $res = Update-DshCustomSkillDirs -PresetPath $dsh.PresetPath -Dir $repoSkills
                    switch ($res) {
                        'updated'        { Write-Host '  已在现有 customSkillDirs 中追加本仓库。'; Set-ComponentStatus 'DeepSeek Harness' 'PASS' '已更新' }
                        'added-config'   { Write-Host '  已为 skill-filesystem 增加 customSkillDirs 配置。'; Set-ComponentStatus 'DeepSeek Harness' 'PASS' '已更新' }
                        'appended-entry' { Write-Host '  预设中缺少 skill-filesystem，已追加完整条目。'; Set-ComponentStatus 'DeepSeek Harness' 'PASS' '已更新' }
                        default          { Write-Host '  customSkillDirs 已包含本仓库。'; Set-ComponentStatus 'DeepSeek Harness' 'PASS' '已是最新' }
                    }
                }
            }
            elseif ($dsh.PresetName) {
                Set-ComponentStatus -Name 'DeepSeek Harness' -Status 'WARN' -Note ("默认预设 {0} 的 agent.cordis.yml 不存在" -f $dsh.PresetName)
                $script:Hints.Add(("DSH 默认预设 {0} 缺失，未自动代建。请先在该 DSH 内初始化一次预设后重跑一键配置。" -f $dsh.PresetName))
            }
            else {
                $presetPath = New-MinimalDshPreset -Home $dsh.Home -Dir $repoSkills
                Write-Host '  未发现任何默认预设，已创建最小预设 ai-shared-skills 并设为默认。'
                Set-ComponentStatus -Name 'DeepSeek Harness' -Status 'PASS' -Note '已创建最小预设'
                $script:Details.Add(("  最小预设位置：{0}" -f $presetPath))
            }
        }
    }
    catch {
        Set-ComponentStatus -Name 'DeepSeek Harness' -Status 'FAIL' -Note $_.Exception.Message
        $script:Hints.Add("DSH 配置失败：可在当前使用预设的 agent.cordis.yml 中为 skill-filesystem 条目添加 config.customSkillDirs 指向 $repoSkills")
    }

    # ----- Codex -----
    Write-Step '[5/5] 安装/刷新 Codex 受控副本'
    try {
        $codex = Get-CodexInfo -OverrideHome $CodexHome
        if (-not $codex.Installed) {
            Write-Host '  未检测到已安装的 Codex，跳过。'
            Set-ComponentStatus -Name 'Codex' -Status 'SKIP' -Note '未检测到安装'
        }
        else {
            Write-Host ("  Codex home：{0}（{1}）" -f $codex.Home, $codex.Source)
            foreach ($skill in $active) {
                $src = Join-Path $repoSkills $skill.name
                if (-not (Test-Path -LiteralPath (Join-Path $src 'SKILL.md'))) {
                    Set-ComponentStatus -Name $skill.name -Status 'WARN' -Note "源目录缺少 SKILL.md：$src"
                    continue
                }
                $res = Sync-CodexSkill -SourceDir $src -SkillsRoot $codex.SkillsDir -Name $skill.name
                switch ($res) {
                    'installed' { Write-Host ("  {0}：已安装到 Codex。" -f $skill.name); Set-ComponentStatus -Name $skill.name -Status 'PASS' -Note '新装' }
                    'refreshed' { Write-Host ("  {0}：检测到差异，旧副本已备份并刷新。" -f $skill.name); Set-ComponentStatus -Name $skill.name -Status 'PASS' -Note '已刷新' }
                    'identical' { Write-Host ("  {0}：副本与源一致。" -f $skill.name); Set-ComponentStatus -Name $skill.name -Status 'PASS' -Note '已是最新' }
                }
                Set-ComponentStatus -Name 'Codex' -Status 'PASS'
            }
        }
    }
    catch {
        Set-ComponentStatus -Name 'Codex' -Status 'FAIL' -Note $_.Exception.Message
        $script:Hints.Add('Codex 安装失败：可稍后重跑一键配置；不影响 Hermes / DSH 的 direct-read 使用。')
    }
}

# ---------- 汇总 ----------
Write-Host ''
Write-Host '============================== 配置结果 =============================='
$skillNames = @()
if ($canContinue -and $active) { $skillNames = @($active | ForEach-Object { $_.name }) }
foreach ($k in $script:ComponentStatus.Keys) {
    if ($skillNames -contains $k) { continue }
    Write-Host (Format-StatusLine -Name $k -Status $script:ComponentStatus[$k])
}
if ($canContinue -and $active) {
    foreach ($s in $active) {
        $st = 'PASS'
        $known = $script:ComponentStatus[$s.name]
        if ($known -eq 'WARN') { $st = 'WARN' }
        Write-Host (Format-StatusLine -Name $s.name -Status $st)
    }
}
Write-Host '======================================================================'

if ($script:Details.Count -gt 0) {
    Write-Host ''
    Write-Host '—— 详细信息 ——'
    foreach ($d in $script:Details) { Write-Host $d }
}
if ($script:Hints.Count -gt 0) {
    Write-Host ''
    Write-Host '—— 下一步建议 ——'
    foreach ($h in $script:Hints) { Write-Host ("  · " + $h) }
}
Write-Host ''

$failed = @($script:ComponentStatus.Values) -contains 'FAIL'
if ($failed) {
    Write-Host '结论：存在失败项，请按上方建议处理后重跑一键配置。'
    exit 1
}
else {
    Write-Host '结论：全部完成。Hermes / DSH 为 direct-read（改仓库即生效）；Codex 为受控副本（重跑一键配置即可刷新）。'
    exit 0
}
