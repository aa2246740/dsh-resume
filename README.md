# dsh-resume

Continue Codex, Claude Code, and Cursor work in DeepSeek Harness.

`dsh-resume` is an unofficial external plugin for DeepSeek Harness RC8. It adds three user-only slash commands:

| Command | Source |
| --- | --- |
| `/resume-codex [latest \| session-id \| path \| title]` | Codex CLI and Codex app sessions |
| `/resume-claude [latest \| session-id \| path \| title]` | Claude Code sessions |
| `/resume-cursor [latest \| session-id \| path \| title]` | Cursor sessions and transcripts |

The command resumes the **work**, not the old process. It reads a local foreign session, converts recoverable history into inert structured data, builds a short handoff, verifies the current repository, and then continues with DSH's own agent and tools.

> This project is not affiliated with or endorsed by DeepSeek, OpenAI, Anthropic, Cursor, xAI, or Grok.

## Why this boundary matters

Foreign session stores contain stale tool output, instructions from another runtime, and sometimes private system or reasoning records. `dsh-resume` deliberately does not replay them.

- Read-only: it never modifies Codex, Claude Code, or Cursor session stores.
- Inert history: recovered messages and tool records are data, never executable instructions.
- No hidden-context import: system prompts, developer instructions, reasoning, signatures, and encrypted or malformed records are excluded or reported unavailable.
- Workspace scoped: automatic discovery uses the current DSH session working directory.
- No guessing: ambiguous titles return candidates and require a user choice.
- Fresh evidence: historical claims stay `HISTORY_REPORTED` until DSH verifies them in the current turn.
- Shell-free adapter: DSH starts the reader with a fixed argument array and bounded output.

## What a successful resume produces

The DSH agent receives a six-part handoff:

1. User goal and last recoverable request.
2. Relevant files, modules, commands, tests, and artifacts.
3. Completed work and the evidence recorded for it.
4. Open work.
5. Exact stopping point and safest next action.
6. Reader warnings and material uncertainty.

Every important completion, test, deployment, publication, compatibility, or activation claim is labeled `CURRENT_OBSERVED`, `HISTORY_REPORTED`, `MISMATCH`, or `UNAVAILABLE`.

## Install from source

Prerequisites:

- DeepSeek Harness `0.1.0-rc.8`
- Node.js `22.19+` or `24+`
- pnpm `11.7.0`
- Python 3 on `PATH`
- `zstd` on `PATH` only when a Codex rollout is Zstandard-compressed
- [dshx](https://github.com/aa2246740/dsh-external-plugin-devkit) for external-plugin checks and activation

Clone the repository as one Harness plugin:

```sh
git clone https://github.com/aa2246740/dsh-resume.git \
  /absolute/path/to/deepseek-harness/my-plugins/dsh-resume
cd /absolute/path/to/deepseek-harness/my-plugins/dsh-resume
corepack pnpm install --frozen-lockfile
pnpm check
```

Then validate it against the intended Harness checkout:

```sh
dshx check dsh-resume --harness /absolute/path/to/deepseek-harness
dshx activation-plan dsh-resume --change patch \
  --harness /absolute/path/to/deepseek-harness
```

Follow the `patch` plan emitted by dshx to add the Host plugin to the profile's watched `cordis.patch.yml`. This Host-only plugin adds no client bundle, so the patch contract itself does not require a browser refresh; still confirm that the slash commands appear. Do not mount it simultaneously through both a profile bundle and a patch entry.

The committed `cordis.yml` points at the built `lib/dsh-resume.js`, so run `pnpm build` before activation. Installing files and activating the current Host are separate states; do not treat a successful clone or build as proof that the slash commands are live.

## Development

```sh
corepack pnpm install
pnpm typecheck
pnpm test
pnpm build
```

The test suite covers the Host registration contract, user-only slash-skill policy, Grok-compatible safety contract, leading-dash argument hardening, Claude/Codex/Cursor fixtures, and inert tool-call handling.

## Grok compatibility

The session reader and six-part handoff contract track Grok's foreign-session resume behavior. The reader currently matches the Grok 1.0.5 bundled reader byte-for-byte:

```text
SHA-256 342853ca19f8d9f10dd171890ee1bbacec2350ea90221cb4ad6925cda2380a58
```

“Compatible” means the same supported local stores, JSON shape, inert-history boundary, ambiguity behavior, and handoff workflow. It does **not** mean restoration of a foreign process, model context, hidden reasoning, permissions, or unrecoverable data.

Grok reserves [`/resume` and `grok --resume`](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/17-sessions.md) for its own native sessions. Its foreign-session skills use the plainer promise “Resume or continue work from …”, and its [slash-command documentation](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/04-slash-commands.md) exposes user-invocable skills through the command menu. `dsh-resume` follows that distinction: it advertises continuation of work, not full-fidelity runtime migration.

## License and attribution

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

The bundled foreign-session reader is derived from the resume-session reader distributed with xAI Grok. Grok and xAI names remain the property of their respective owners. DeepSeek Harness itself is licensed separately by DeepSeek.
