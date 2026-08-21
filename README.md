# dsh-resume

[中文](README.md) · [English](README.en.md)

在 DeepSeek Harness 里，接着做 Codex、Claude Code、Cursor、Grok、Pi 没做完的那件事。

输入 `/resume-claude`（另外四条同理）。它只读本机那次会话，抽出还能接手的上下文，写成一张交接卡。旧进程不会被拉起来，别人的会话文件也不会被改。

非官方插件，和 DeepSeek、OpenAI、Anthropic、Cursor、xAI、Pi 都没有关系。

## 它长什么样

这台环境没能启动完整的 DeepSeek Harness Web。下面是本仓库自带的 reader，对着公开演示会话跑出来的真输出——插件在 DSH 里读到的就是这份东西。

![六段交接：目标、文件、做到哪、还差什么、下一步。Grok 的隐藏推理被丢掉了。](docs/screenshots/handoff.gif)

标题对不上号时，它不会猜，会把候选列出来让你选。

![`/resume-claude checkout` 命中两条会话，列出 id 和标题等你挑。](docs/screenshots/candidates.png)

读进来的历史带着醒目标记：这是 inert 数据，不是给你再执行一遍的。

![bundled human renderer：INERT FOREIGN HISTORY，工具调用标成 inert。](docs/screenshots/inert-history.png)

JSON 里每一轮、每一次工具调用都带着 `inert: true`。

![reader JSON：turns 和 tool_calls 都标了 inert: true。](docs/screenshots/json-inert.png)

自动发现只扫当前工作目录。

![`claude list` 只列出这个目录里的两条 Claude 会话。](docs/screenshots/session-list.png)

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
