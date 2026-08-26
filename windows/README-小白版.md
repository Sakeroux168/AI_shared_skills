# AI_shared_skills · Windows 小白使用说明

这个仓库里放的是给 AI 助手用的"专业 Skill"。你不需要懂任何配置字段，只要会用下面两个文件：

| 文件 | 作用 |
|---|---|
| `一键配置.cmd` | 让你电脑上的 Codex / Hermes / DeepSeek Harness 自动接上本仓库的 Skill |
| `一键检查.cmd` | 检查现在的接入状态是否正常，坏了会告诉你怎么修 |

---

## 第一次怎么用

1. 把本仓库下载或 clone 到电脑上的**任意文件夹**（比如桌面、D 盘都行，路径里有中文也没关系）。
2. 打开这个 `windows` 文件夹。
3. **双击 `一键配置.cmd`**，等它跑完。
4. 结尾出现类似下面的结果就是成功了：

```
AI_shared_skills Registry [PASS]
Codex [PASS]
Hermes [PASS]
DeepSeek Harness [PASS]
gpt-image-2-style-library [PASS]
```

没有安装的组件会显示 `[SKIP]`（跳过），不影响其他组件。

## 换电脑 / 重装系统后怎么恢复

1. 新电脑上先装好你要用的 AI 工具（Codex、Hermes 或 DeepSeek Harness）。
2. 把本仓库重新 clone/下载到新电脑任意位置。
3. 双击 `一键配置.cmd`。完事。

## 本地的 AI_shared_skills 文件夹被删了怎么办

不用慌：**GitHub 上的 [Sakeroux168/AI_shared_skills](https://github.com/Sakeroux168/AI_shared_skills) 才是正式主仓**，你电脑上这份只是"运行镜像"，随时可以重新生成。

1. 重新 clone/下载主仓到任意位置。
2. 双击新位置里的 `一键配置.cmd`。

它会自动把 Hermes、DSH 的指向改到新位置，并把 Codex 的副本刷新成最新版。

## 怎么检查有没有坏

双击 `一键检查.cmd`。每一行都会给出 PASS / WARN / FAIL / SKIP 和中文解释；FAIL/WARN 后面跟着"修复建议"，照着做即可。最常见的修复方式就一个：重跑 `一键配置.cmd`。

## 什么情况需要重启 Hermes / DSH

- 这两个工具是"直接读仓库"模式：仓库内容更新后，**新开的会话**自动生效。
- 如果你有一个一直开着的旧窗口/长会话，想让它立刻看到新配置或新 Skill，把它关掉重开就行。
- Codex 是"副本"模式：仓库更新后需要重跑 `一键配置.cmd` 来刷新副本（旧的会自动备份）。

## 常见问题

- **显示某个工具 SKIP？** 说明电脑上没装它，装好后重跑一键配置即可。
- **重复运行一键配置有影响吗？** 没有。它只会补缺、刷新，不会产生重复配置，也不会动你无关的 Skill 和设置。
- **运行前会备份我的配置吗？** 会。每次改动前都自动备份到 `%LOCALAPPDATA%\AI_shared_skills\backups\` 里（不在仓库内，不会被上传）。
- **DSH 提示 npx 缓存警告？** 说明 DSH 运行时装在临时缓存里，清理缓存后会坏。按提示执行 `npm install -g @deepseek-ai/dsh@当前版本号` 再正常启动一次 dsh 即可迁移到持久安装。
