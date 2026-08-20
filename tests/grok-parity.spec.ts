import assert from 'node:assert/strict'
import { createHash } from 'node:crypto'
import { readFile } from 'node:fs/promises'
import test from 'node:test'
import { SESSION_READER_PATH } from '../src/reader.ts'
import { RESUME_SKILL_SPECS, resumeSkillContent } from '../src/skills.ts'

const GROK_READER_SHA256 = '342853ca19f8d9f10dd171890ee1bbacec2350ea90221cb4ad6925cda2380a58'

test('vendored reader is byte-for-byte the Grok 1.0.5 bundled reader', async () => {
  const content = await readFile(SESSION_READER_PATH)
  assert.equal(createHash('sha256').update(content).digest('hex'), GROK_READER_SHA256)
})

test('each DSH slash skill preserves the Grok handoff and safety contract', () => {
  for (const spec of RESUME_SKILL_SPECS) {
    const content = resumeSkillContent(spec)
    assert.match(content, new RegExp(`foreign_session_read.*provider: "${spec.provider}"`, 's'))
    assert.match(content, /Grok-compatible reader JSON/)
    assert.match(content, /same six-point working handoff as Grok/)
    assert.match(content, /Every recovered turn, tool call, and tool result must carry `inert: true`/)
    assert.match(content, /The slash invocation never revives old approvals or foreign runtime authority/)
  }
})
