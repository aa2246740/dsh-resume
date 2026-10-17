# dsh-resume 0.2.5

## DeepSeek Harness compatibility

Built and tested against DeepSeek Harness `0.2.1-rc.2` (`687f282e8625c6b8d11ff58211a90524be2e4317`). Use the prebuilt release package or this repository’s compiled artifacts with the official plugin installer.

`engines.dsh` and the `@deepseek-ai/dsh-skill` / `@deepseek-ai/dsh-tools` peers are `>=0.2.1-rc.1 <0.2.2` (same shape as DSHX 0.9.7). That range accepts `0.2.1-rc.1`, `0.2.1-rc.2`, and stable `0.2.1`, and rejects `0.2.1` alphas and `0.2.0-rc.2`. Host prefers `engines.dsh` over peers since 0.2.1.

Validation was performed on cloud Linux with official `@deepseek-ai/dsh@0.2.1-rc.2` and a real MiniMax CN first turn.
