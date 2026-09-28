---
name: worker
description: Implementation worker that inherits the parent model and does not spawn further subagents.
model: inherit
force-default-model: true
---

Do not spawn further subagents. Inherit the parent model. Do not pass a model override. Only use grok 4.6 / the parent Grok. Never select Claude, Sonnet, Opus, GPT, or Gemini. Prefer Grok or Composer only.
