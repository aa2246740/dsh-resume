# dsh-resume

[中文](README.md) · [English](README.en.md)

在 DeepSeek Harness 里，接着做 Codex、Claude Code、Cursor、Grok、Pi 没做完的那件事。

输入 `/resume-claude`（另外四条同理）。它只读本机那次会话，抽出还能接手的上下文，写成一张交接卡。旧进程不会被拉起来，别人的会话文件也不会被改。

非官方插件，和 DeepSeek、OpenAI、Anthropic、Cursor、xAI、Pi 都没有关系。

## 它长什么样

下面是官方 DeepSeek Harness Web。演示内容是公开的结账小工具会话（税额取整），不是谁的私人记录。

在官方 composer 里输入 `/resume-claude`，斜杠技能会出现。

![官方 DeepSeek Harness composer，已输入 /resume-claude，Chrome 地址栏可见。](docs/screenshots/composer-resume-claude.png)

输入 `/resume-claude latest`，交接卡写在当前 DSH 会话里。

![在官方 composer 发送 /resume-claude latest，当前会话里出现六段交接。](docs/screenshots/handoff.gif)

六段按 Grok 那套来：目标、文件、做到哪、还差什么、停在哪、读者警告。

![DSH 会话里的六段交接：做到哪、还差 0.5 分的取整、下一步。](docs/screenshots/handoff.png)

标题对不上号时，它不会猜。官方界面会列出候选让你挑。

![`/resume-claude checkout` 命中两条会话，官方选择器列出税额取整和运费估算。](docs/screenshots/candidates.png)

## 装上

DeepSeek Harness `0.1.0-rc.8`，Node.js `22.19+` 或 `24+`，pnpm `11.7`，Python 3。Codex 的压缩 rollout 才需要 `zstd`。检查和激活用 [dshx](https://github.com/aa2246740/dsh-external-plugin-devkit)。

```sh
git clone https://github.com/aa2246740/dsh-resume.git \
  /absolute/path/to/deepseek-harness/my-plugins/dsh-resume
cd /absolute/path/to/deepseek-harness/my-plugins/dsh-resume
corepack pnpm install --frozen-lockfile
pnpm build
dshx check dsh-resume --harness /absolute/path/to/deepseek-harness
dshx activation-plan dsh-resume --change patch \
  --harness /absolute/path/to/deepseek-harness
```

按 dshx 给出的 `patch` 计划，把这条 Host 插件写进 profile 的 `cordis.patch.yml`。它没有 client 包，一般不用刷新浏览器，但要确认斜杠命令已经出现。不要同时用 bundle 和 patch 挂两份。

`cordis.yml` 指向编好的 `lib/dsh-resume.js`，所以得先 `pnpm build`。克隆成功不等于命令已经活了。

## 接着做，不是把旧进程拉起来

只读，不改任何一家的会话仓库。系统提示、隐藏推理、加密或坏掉的记录要么丢掉，要么标明不可用。历史里的结论先标成 `HISTORY_REPORTED`，这轮在当前仓库里核对过的才是 `CURRENT_OBSERVED`。Grok 只读看得见的 `updates.jsonl`；Pi 只跟当前这条分支。

| 命令 | 从哪接着 |
| --- | --- |
| `/resume-codex [latest \| 会话 id \| 路径 \| 标题]` | Codex CLI / 应用 |
| `/resume-claude [latest \| 会话 id \| 路径 \| 标题]` | Claude Code |
| `/resume-cursor [latest \| 会话 id \| 路径 \| 标题]` | Cursor |
| `/resume-grok [latest \| 会话 id \| 路径 \| 标题]` | Grok |
| `/resume-pi [latest \| 会话 id \| 路径 \| 标题]` | Pi |

## 开发

```sh
corepack pnpm install
pnpm check
```

## 许可

Apache-2.0。见 [LICENSE](LICENSE) 和 [NOTICE](NOTICE)。
