# dsh-resume

[中文](README.md)

Bring local Codex, Claude Code, Cursor, Grok, Pi, Trae, and ZCode session context into DeepSeek Harness to continue unfinished work.

## Install

**Version 0.2.4 is verified against DeepSeek Harness 0.1.7-rc.2.** Both the package and repository contain compiled plugin files; no Harness source checkout or local build is required. Python 3 is required to read history. Compressed Codex rollouts additionally require `zstd`.

### Official Desktop app

1. Open **Plugins → Add plugin** (under Settings in some versions).
2. Enter `github:aa2246740/dsh-resume#v0.2.4` in **Package name or address**, then install and enable it.
3. Follow the installer's activation instructions. Type `/resume-` in the composer and check that all seven commands below appear.

Alternatively, download `dsh-resume-0.2.4.tgz` from the [v0.2.4 Release](https://github.com/aa2246740/dsh-resume/releases/tag/v0.2.4) and enter its absolute path in the same installer. Desktop uses its own profile; do not use Web Host commands to install into Desktop.

### Web Host

Use the official CLI:

```sh
dsh plugin --profile web add github:aa2246740/dsh-resume#v0.2.4
```

Or, from the downloaded archive's directory:

```sh
dsh plugin --profile web add ./dsh-resume-0.2.4.tgz
```

The official `dsh` command and pnpm must be available. Node.js must be `^22.19.0` or `>=24.0.0`. Use the existing Web Host's `DSH_HOME`. This only installs into the Web profile, not Desktop. Follow the official installer's activation result. If it requests a restart, exit and reopen the original Host normally; do not start another Host alongside it.

### Upgrade and remove

Repeat the matching installation steps to upgrade. If migrating from a manual mount, disable the old duplicate entry and retain only the package's `dsh-resume` instance.

Remove through the Desktop plugin manager, or for Web:

```sh
dsh plugin --profile web remove dsh-resume
```

## Usage

Type `/resume-claude`, or the matching command for the other six. The plugin reads that local session, pulls context that can still be handed off, and writes a card into the current DSH chat. It does not restart the old process or rewrite anyone else's session files.

![Composer with /resume-claude typed](docs/screenshots/composer-resume-claude.png)

![Sending /resume-claude latest writes a six-section handoff](docs/screenshots/handoff.gif)

![Handoff card: done, remaining, next](docs/screenshots/handoff.png)

![Two title matches listed as candidates](docs/screenshots/candidates.png)

The six sections are objective, files, done, remaining, stopped at, and reader warnings. If a title is ambiguous it lists candidates instead of guessing.

## Commands

Read-only. Foreign session stores are not modified. System prompts, hidden reasoning, encrypted or corrupt records are dropped or marked unavailable. History conclusions start as `HISTORY_REPORTED`. Only facts checked in the current workspace this turn are `CURRENT_OBSERVED`. Grok reads visible `updates.jsonl` only. Pi follows the current branch only. ZCode reads `cli/db/db.sqlite` only and does not replay calls or revive the CLI. Compaction is a warning; older rows still in the database are kept. Abandoned `v2/sessions` and `cli/rollout` JSONL are not the primary store. Projects JSONL is a warned fallback only when sqlite is absent. Trae reads `ModularData/ai-agent/database.db` only (`TRAE_HOME` / `TRAE_AGENT_DIR` override). SQLCipher 4 is opened as a private snapshot and never written back; Trae is not revived. `~/.trae`, TinyStorage, Chromium Session Storage, and `state.vscdb` are not transcripts.

| Command | Source |
| --- | --- |
| `/resume-codex [latest \| session id \| path \| title]` | Codex CLI / app |
| `/resume-claude [latest \| session id \| path \| title]` | Claude Code |
| `/resume-cursor [latest \| session id \| path \| title]` | Cursor |
| `/resume-grok [latest \| session id \| path \| title]` | Grok |
| `/resume-pi [latest \| session id \| path \| title]` | Pi |
| `/resume-trae [latest \| session id \| path \| title]` | Trae |
| `/resume-zcode [latest \| session id \| path \| title]` | ZCode |

## Develop

```sh
corepack pnpm install
pnpm check
```

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
