# Cloud agent policy

Never launch subagents (Task/explore/browser/computerUse/video) with other models. Only use grok 4.6. Never Claude/GPT/Gemini; stay on parent Grok. Do not spawn Task/CU/browser unless explicitly asked; if a subagent is required, inherit parent model (do not pass model). Prefer Grok or Composer only.

Never launch Task, explore, browser, computerUse, or video with another model. Do not spawn other-model subagents. Never select Claude, GPT, or Gemini. Stay on the parent Grok.
