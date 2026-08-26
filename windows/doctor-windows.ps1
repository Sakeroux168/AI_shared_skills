# AI_shared_skills 一键检查（Windows）
# 用法：双击 windows\一键检查.cmd。只读检查，不修改任何配置。

param(
    [string] $HermesHome,
    [string] $DshHome,
    [string] $CodexHome
)

$ErrorActionPreference = 'Continue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

Import-Module (Join-Path $PSScriptRoot '_lib.psm1') -DisableNameChecking

$script:Rows = New-Object System.Collections.Generic.List[hashtable]
$script:Hints = New-Object System.Collections.Generic.List[string]

function Add-Result {
    param([string] $Item, [ValidateSet('PASS','WARN','FAIL','SKIP')] [string] $Status, [string] $Note = '', [string] $Fix = '')
    $script:Rows.Add(@{ Item = $Item; Status = $Status; Note = $Note; Fix = $Fix })
    if ($Fix) { $script:Hints.Add(($Fix)) }
}

function Test-GitRepo {
    param([string] $Root)
    $gitDir = Join-Path $Root '.git'
    if (-not (Test-Path -LiteralPath $gitDir)) { return @{ Ok = $false; Msg = '不是 Git 仓库（可能是直接下载的 ZIP）' } }
    $head = & git -C $root rev-parse HEAD 2>$null
    if ($LASTEXITCODE -ne 0) { return @{ Ok = $false; Msg = 'git 仓库存在但无法读取 HEAD' } }
    $remote = & git -C $root remote get-url origin 2>$null
    $isOrigin = ($remote -match 'Sakeroux168/AI_shared_skills')
    return @{ Ok = $true; Msg = ("HEAD {0}{1}" -f $head.Substring(0, [Math]::Min(9, $head.Length)), $(if ($isOrigin) { "，origin=官方主仓" } else { "（无 origin 或非官方远端）" })) }
}

Write-AissBanner -Steps @(
    'Git 仓库与 Registry 健康度',
    '当前 AI_shared_skills 路径与启用中的 Skill',
    'Hermes 配置与运行时发现',
    'DeepSeek Harness 运行时与 customSkillDirs',
    'Codex 受控副本一致性'
)

# ---------- 1. 仓库 / Registry ----------
Write-Step '[1/5] 仓库与 Registry'
$repoOk = $false
try {
    $ctx = Get-AissContext -WindowsDir $PSScriptRoot
    if (-not $ctx.Valid) { throw $ctx.Error }
    $g = Test-GitRepo -Root $ctx.Root
    if (-not $g.Ok) { Add-Result 'Git 仓库' 'WARN' $g.Msg '建议用 git clone 从 GitHub 主仓获取，以便后续更新。' }
    else { Add-Result 'Git 仓库' 'PASS' $g.Msg }
    $reg = Read-AissRegistry -Path $ctx.RegistryPath
    if (-not $reg.Ok) { Add-Result 'Registry (skills.json)' 'FAIL' $reg.Msg '请重新下载本仓库；若持续失败请在 GitHub 提 issue。' }
    else { Add-Result 'Registry (skills.json)' 'PASS'; $repoOk = $true; $script:Ctx = $ctx; $script:Reg = $reg }
}
catch {
    Add-Result '仓库结构' 'FAIL' $_.Exception.Message '请重新从 GitHub 下载/clone AI_shared_skills。'
}

if ($repoOk) {
    Write-Host ('  当前仓库路径：' + $script:Ctx.Root)
    Add-Result 'AI_shared_skills 路径' 'PASS' $script:Ctx.Root
    foreach ($s in (Get-AissActiveSkills -RegistryData $script:Reg.Data)) {
        $trust = $s.trust_status
        if ($trust -eq 'trusted') { Add-Result ("Registry · " + $s.name) 'PASS' ("status={0} trust={1} upstream={2}" -f $s.local.status, $trust, $s.upstream_commit) }
        else { Add-Result ("Registry · " + $s.name) 'WARN' ("trust={0}" -f $trust) '该 Skill 未通过信任审核，一键配置不会安装它到 Codex。' }
    }
}

# ---------- 2. Hermes ----------
Write-Step '[2/5] Hermes'
$hermes = Get-HermesInfo -OverrideHome $HermesHome
if (-not $hermes.Installed) {
    Add-Result 'Hermes' 'SKIP' '未检测到安装' '如需使用 Hermes：先安装 Hermes，再重跑一键配置。'
}
else {
    $cfgText = Read-TextAuto $hermes.ConfigPath
    if ($null -eq $cfgText) {
        Add-Result 'Hermes 配置' 'FAIL' ("config.yaml 不存在：{0}" -f $hermes.ConfigPath) '运行 windows\一键配置.cmd 即可自动创建。'
    }
    elseif (Test-HermesConfigListsDir -ConfigText $cfgText -NormalizedDir (Get-NormalizedDir $script:Ctx.SkillsPath)) {
        Add-Result 'Hermes 配置 external_dirs' 'PASS' $hermes.ConfigPath
        # 尽力而为的“实际发现”验证：借用本机 Hermes 自带代码
        $verified = $false
        try {
            $cmd = Get-Command hermes.exe -ErrorAction SilentlyContinue
            if (-not $cmd) { $cmd = Get-Command hermes -ErrorAction SilentlyContinue }
            if ($cmd) {
                $anchor = $cmd.Source
                for ($i = 0; $i -lt 6 -and $anchor; $i++) {
                    $cand = Split-Path -Parent $anchor
                    if ([string]::IsNullOrEmpty($cand) -or $cand -eq $anchor) { break }
                    if (Test-Path -LiteralPath (Join-Path $cand 'agent\skill_utils.py')) {
                        $py = Join-Path $cand 'venv\Scripts\python.exe'
                        if (-not (Test-Path -LiteralPath $py)) { $py = 'python' }
                        $probe = Join-Path (Get-AissStateDir) ('probe-hermes-' + [guid]::NewGuid().ToString('N').Substring(0,6) + '.py')
                        $code = @"
import json, sys
sys.path.insert(0, r'$cand')
from agent.skill_utils import get_external_skills_dirs, iter_skill_index_files
dirs = [str(p) for p in get_external_skills_dirs()]
hits = []
for d in get_external_skills_dirs():
    hits += [str(f) for f in iter_skill_index_files(d, 'SKILL.md')]
print(json.dumps({'dirs': dirs, 'hits': hits}))
"@
                        [System.IO.File]::WriteAllText($probe, $code, (New-Object System.Text.UTF8Encoding($false)))
                        $out = & $py $probe 2>$null
                        Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
                        $j = (@($out) | Select-Object -First 50) -join "`n"
                        $m = [regex]::Match($j, '\{.*\}', 'Singleline')
                        if ($m.Success) {
                            $data = $m.Value | ConvertFrom-Json
                            $want = (Get-NormalizedDir $script:Ctx.SkillsPath)
                            $found = @($data.hits | Where-Object { (Get-NormalizedDir (Split-Path -Parent $_)) -like ($want + '\*') }).Count
                            if ($found -gt 0) { Add-Result 'Hermes 实际发现' 'PASS' ("loader 在 external_dirs 中发现 {0} 个 SKILL.md" -f $data.hits.Count); $verified = $true }
                        }
                        break
                    }
                    $anchor = $cand
                }
            }
            if (-not $verified) { Add-Result 'Hermes 实际发现' 'SKIP' '未能在本机自动定位可执行的 Hermes 代码，跳过深度验证（不影响配置本身）' '可在 Hermes 会话里输入 skills 相关命令确认列表。' }
        }
        catch {
            Add-Result 'Hermes 实际发现' 'SKIP' ('深度验证未执行：' + $_.Exception.Message)
        }
    }
    else {
        Add-Result 'Hermes 配置 external_dirs' 'FAIL' ("配置中未见本仓库 skills 路径（{0}）" -f $hermes.ConfigPath) '运行 windows\一键配置.cmd 自动补齐。'
    }
}

# ---------- 3. DSH ----------
Write-Step '[3/5] DeepSeek Harness'
$dsh = Get-DshInfo -OverrideHome $DshHome
if (-not $dsh.Installed) {
    Add-Result 'DeepSeek Harness' 'SKIP' '未检测到安装' '如需使用 DSH：先安装并初始化，再重跑一键配置。'
}
else {
    $stab = Get-DshRuntimeStability -DshInfo $dsh
    if ($stab.Version) { Add-Result 'DSH 运行时版本' 'PASS' $stab.Version }
    if ($stab.Stable) { Add-Result 'DSH runtime 稳定性' 'PASS' '未发现 npx 缓存依赖' }
    else {
        foreach ($r in $stab.Reasons) { Add-Result 'DSH runtime 稳定性' 'WARN' $r '修复：npm install -g @deepseek-ai/dsh@当前版本 后正常启动一次 dsh（会自动迁移链接）。不要直接清理 npx 缓存。' }
    }
    if ($dsh.PresetName -and (Test-Path -LiteralPath $dsh.PresetPath)) {
        $ptext = Read-TextAuto $dsh.PresetPath
        if ($ptext -and ((Get-NormalizedDir $script:Ctx.SkillsPath) -eq '' -or (Test-DshPresetListsDir -PresetText $ptext -NormalizedDir (Get-NormalizedDir $script:Ctx.SkillsPath)))) {
            Add-Result 'DSH customSkillDirs' 'PASS' $dsh.PresetPath
            # 深度验证：用稳定 runtime 的 provider 实际跑一次 discovery+load
            try {
                $node = Get-Command node.exe -ErrorAction SilentlyContinue
                $pkgCandidates = @()
                try {
                    $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
                    if ($npmCmd) {
                        $npmRoot = (& npm.cmd root -g 2>$null)
                        if ($npmRoot) {
                            $pkgCandidates += (Join-Path $npmRoot '@deepseek-ai\dsh-skill-filesystem')
                            $pkgCandidates += (Join-Path $npmRoot '@deepseek-ai\dsh\node_modules\@deepseek-ai\dsh-skill-filesystem')
                        }
                    }
                } catch { }
                $pkgCandidates += (Join-Path $env:APPDATA 'npm\node_modules\@deepseek-ai\dsh-skill-filesystem')
                $pkg = $pkgCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
                if ($node -and $pkg) {
                    $probe = Join-Path (Get-AissStateDir) ('probe-dsh-' + [guid]::NewGuid().ToString('N').Substring(0,6) + '.mjs')
                    $code = @"
import { pathToFileURL } from 'node:url';
import { readFileSync } from 'node:fs';
const pkgUrl = pathToFileURL(process.argv[2] + '\\lib\\index.js');
const { FileSystemSkillProvider } = await import(pkgUrl);
const dir = process.argv[3];
const p = new FileSystemSkillProvider({ get: () => undefined, logger: { warn: () => {} } }, { invalidate: () => {}, signal: new AbortController().signal }, { dshHome: '.', includeDefaultRoots: false, customSkillDirs: [dir] });
const cands = await p.list({});
const hit = cands.find(c => c.name === process.argv[4]);
if (!hit) { console.log(JSON.stringify({ ok: false })); process.exit(0); }
const full = await p.get(hit, {});
console.log(JSON.stringify({ ok: !!full.content, bytes: full.content ? full.content.length : 0 }));
await p.dispose();
"@
                        [System.IO.File]::WriteAllText($probe, $code, (New-Object System.Text.UTF8Encoding($false)))
                        $firstActive = (Get-AissActiveSkills -RegistryData $script:Reg.Data) | Select-Object -First 1
                        $out = & $node.Source $probe $pkg $script:Ctx.SkillsPath $firstActive.name 2>$null
                        Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
                        $j = $out | Where-Object { $_ -match '^\{' } | Select-Object -Last 1
                        if ($j) {
                            $data = $j | ConvertFrom-Json
                            if ($data.ok) { Add-Result 'DSH 实际发现+加载' 'PASS' ("provider list/get 成功（{0} 字符）" -f $data.bytes) }
                            else { Add-Result 'DSH 实际发现+加载' 'FAIL' 'provider 未发现目标 Skill' '重跑一键配置；若仍失败请检查预设文件。' }
                        }
                        else { Add-Result 'DSH 实际发现+加载' 'SKIP' 'provider 探针无输出' }
                    }
                    else { Add-Result 'DSH 实际发现+加载' 'SKIP' '未找到 node 或全局 dsh-skill-filesystem 包' }
                }
                catch {
                    Add-Result 'DSH 实际发现+加载' 'SKIP' ('深度验证未执行：' + $_.Exception.Message)
                }
        }
        else {
            Add-Result 'DSH customSkillDirs' 'FAIL' ("预设 {0} 未包含本仓库 skills 路径" -f $dsh.PresetName) '运行 windows\一键配置.cmd 自动补齐。'
        }
    }
    elseif ($dsh.PresetName) {
        Add-Result 'DSH customSkillDirs' 'WARN' ("默认预设 {0} 文件缺失" -f $dsh.PresetName) '在 DSH 内重新初始化预设后重跑一键配置。'
    }
    else {
        Add-Result 'DSH customSkillDirs' 'FAIL' 'settings.yaml 无默认预设' '运行 windows\一键配置.cmd 会创建最小预设。'
    }
}

# ---------- 4. Codex ----------
Write-Step '[4/5] Codex 受控副本'
$codex = Get-CodexInfo -OverrideHome $CodexHome
if (-not $codex.Installed) {
    Add-Result 'Codex' 'SKIP' '未检测到安装' '如需使用 Codex Skills：先安装 Codex，再重跑一键配置。'
}
elseif ($repoOk) {
    foreach ($skill in (Get-AissActiveSkills -RegistryData $script:Reg.Data)) {
        $src = Join-Path $script:Ctx.SkillsPath $skill.name
        $dst = Join-Path $codex.SkillsDir $skill.name
        if (-not (Test-Path -LiteralPath $dst)) {
            Add-Result ("Codex · " + $skill.name) 'FAIL' '尚未安装副本' '运行 windows\一键配置.cmd 一键安装。'
            continue
        }
        $a = Get-TreeFingerprint $src
        $b = Get-TreeFingerprint $dst
        $ak = @($a.Keys); $bk = @($b.Keys)
        $same = ($ak.Count -eq $bk.Count) -and (-not (Compare-Object $ak $bk)) -and (@($ak | Where-Object { $a[$_] -ne $b[$_] }).Count -eq 0)
        if ($same) { Add-Result ("Codex · " + $skill.name) 'PASS' '副本与源逐文件一致' }
        else { Add-Result ("Codex · " + $skill.name) 'WARN' '副本与源不一致（源已更新或副本被改动）' '运行 windows\一键配置.cmd 刷新副本（旧副本会自动备份）。' }
    }
}

# ---------- 汇总 ----------
Write-Host ''
Write-Host '============================== 检查结果 =============================='
foreach ($r in $script:Rows) { Write-Host (Format-StatusLine -Name $r.Item -Status $r.Status -Note $r.Note) }
Write-Host '======================================================================'
if ($script:Hints.Count -gt 0) {
    Write-Host ''
    Write-Host '—— 修复建议 ——'
    $seen = @{}
    foreach ($h in $script:Hints) { if (-not $seen[$h]) { $seen[$h] = $true; Write-Host ("  · " + $h) } }
}
Write-Host ''

$fail = @($script:Rows | Where-Object { $_.Status -eq 'FAIL' })
$warn = @($script:Rows | Where-Object { $_.Status -eq 'WARN' })
if ($fail.Count -gt 0) { Write-Host '结论：存在问题需要处理（见 FAIL 行）。'; exit 1 }
elseif ($warn.Count -gt 0) { Write-Host '结论：整体可用，但有不影响使用的提醒（见 WARN 行）。'; exit 0 }
else { Write-Host '结论：一切正常。'; exit 0 }
