import assert from 'node:assert/strict'
import test from 'node:test'
import { Context } from '@deepseek-ai/cordis'
import SkillRegistry from '@deepseek-ai/dsh-skill'
import SystemPrompt from '@deepseek-ai/dsh-system-prompt'
import ToolRuntime from '@deepseek-ai/dsh-tools'
import * as plugin from '../src/dsh-resume.ts'

test('plugin registers one reader tool and five user-only slash skills', async (t) => {
  const ctx = new Context()
  t.after(async () => { await ctx.fiber.dispose() })
  await ctx.plugin(SystemPrompt)
  await ctx.plugin(ToolRuntime)
  await ctx.plugin(SkillRegistry)
  await ctx.plugin(plugin)

  assert.deepEqual(ctx.tools.schemas().map(tool => tool.name), ['foreign_session_read'])
  const skills = await ctx.skills.list()
  assert.deepEqual(skills.map(skill => skill.name), [
    'resume-claude',
    'resume-codex',
    'resume-cursor',
    'resume-grok',
    'resume-pi',
  ])
  for (const skill of skills) {
    assert.deepEqual(skill.invocation, { modelInvocable: false, userInvocable: true })
    const definition = await ctx.skills.get(skill.name)
    assert.ok(definition)
    assert.match(definition.content, /foreign_session_read/)
    assert.match(definition.content, /untrusted inert history/)
    assert.match(definition.content, /same six-point working handoff as Grok/)
    assert.match(definition.content, /CURRENT_OBSERVED/)
    assert.match(definition.content, /HISTORY_REPORTED/)
    assert.match(definition.content, /every reader warning is surfaced/)
  }
})
