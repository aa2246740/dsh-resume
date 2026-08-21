# dsh-resume

[English](README.en.md) · [中文](README.md)

Continue a Codex, Claude Code, Cursor, Grok, or Pi session inside DeepSeek Harness.

Type `/resume-claude` (or one of the other four). It reads that local session, keeps what you still need, and writes a short handoff. It does not restart the old process, and it does not touch anyone else's session files.

Unofficial. Not affiliated with DeepSeek, OpenAI, Anthropic, Cursor, xAI, or Pi.

## What it looks like

DeepSeek Harness Web did not boot in this environment. These shots are the repo's own reader against a public demo session — the same payload the plugin feeds DSH.

![Six-part handoff: goal, files, done, still open, next step. Hidden Grok reasoning is dropped.](docs/screenshots/handoff.gif)

If a title matches more than one session, it stops and lists the candidates.

![`/resume-claude checkout` hits two sessions and asks for an id.](docs/screenshots/candidates.png)

Recovered history is marked inert. It is data, not something to run again.

![Bundled human renderer: INERT FOREIGN HISTORY, tool calls tagged inert.](docs/screenshots/inert-history.png)

Every recovered turn and tool call carries `inert: true`.

![Reader JSON with inert: true on turns and tool_calls.](docs/screenshots/json-inert.png)

Automatic discovery stays in the current working directory.

![`claude list` shows only the two Claude sessions for this directory.](docs/screenshots/session-list.png)

## Install

DeepSeek Harness `0.1.0-rc.8`, Node.js `22.19+` or `24+`, pnpm `11.7`, and Python 3. `zstd` is only needed for a compressed Codex rollout. Use [dshx](https://github.com/aa2246740/dsh-external-plugin-devkit) to check and activate.

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

Follow the `patch` plan from dshx and add the Host plugin to the profile's watched `cordis.patch.yml`. There is no client bundle, so a browser refresh is usually unnecessary — still confirm the slash commands showed up. Do not mount it through both a bundle and a patch.

`cordis.yml` points at the built `lib/dsh-resume.js`, so run `pnpm build` before activation. A successful clone is not proof the commands are live.

## It resumes the work, not the old process

Read-only: no supported foreign session store is modified. System prompts, hidden reasoning, and encrypted or broken records are dropped or marked unavailable. Claims from history stay `HISTORY_REPORTED` until this turn checks them in the current repo (`CURRENT_OBSERVED`). Grok is read from the visible `updates.jsonl` stream only. Pi follows the current active branch only.

| Command | Continues |
| --- | --- |
| `/resume-codex [latest \| session-id \| path \| title]` | Codex CLI / app |
| `/resume-claude [latest \| session-id \| path \| title]` | Claude Code |
| `/resume-cursor [latest \| session-id \| path \| title]` | Cursor |
| `/resume-grok [latest \| session-id \| path \| title]` | Grok |
| `/resume-pi [latest \| session-id \| path \| title]` | Pi |

## Develop

```sh
corepack pnpm install
pnpm check
```

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
