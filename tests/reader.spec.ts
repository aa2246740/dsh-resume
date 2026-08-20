import assert from 'node:assert/strict'
import { mkdtemp, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import test from 'node:test'
import { buildReaderArgs, runSessionReader } from '../src/reader.ts'

test('buildReaderArgs keeps a leading-dash reference inert', () => {
  assert.deepEqual(buildReaderArgs({
    provider: 'codex',
    action: 'show',
    cwd: '/work/project',
    reference: '  --not-an-option  ',
  }), [
    'codex',
    'show',
    '--cwd',
    resolve('/work/project'),
    '--within-min',
    '0',
    '--max-tool-chars',
    '300',
    '--json',
    '--',
    '--not-an-option',
  ])
})

test('list rejects a session reference instead of guessing', () => {
  assert.throws(() => buildReaderArgs({
    provider: 'cursor',
    action: 'list',
    cwd: '/work/project',
    reference: 'anything',
  }), /does not accept a reference/)
})

test('vendored reader returns the Grok JSON schema for a Claude fixture', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'dsh-resume-foreign-'))
  t.after(async () => { await rm(root, { recursive: true, force: true }) })
  const transcript = join(root, 'fixture-session.jsonl')
  const records = [
    {
      type: 'user',
      uuid: 'user-1',
      parentUuid: null,
      cwd: root,
      gitBranch: 'fixture',
      timestamp: '2026-08-20T00:00:00.000Z',
      message: { role: 'user', content: [{ type: 'text', text: 'Fix the fixture widget.' }] },
    },
    {
      type: 'assistant',
      uuid: 'assistant-1',
      parentUuid: 'user-1',
      cwd: root,
      gitBranch: 'fixture',
      timestamp: '2026-08-20T00:01:00.000Z',
      message: {
        id: 'message-1',
        role: 'assistant',
        content: [
          { type: 'text', text: 'Updated widget.ts and ran its focused test.' },
          { type: 'tool_use', id: 'call-1', name: 'Bash', input: { command: 'npm test' } },
        ],
      },
    },
  ]
  await writeFile(transcript, `${records.map(record => JSON.stringify(record)).join('\n')}\n`)

  const result = JSON.parse(await runSessionReader({
    provider: 'claude',
    action: 'show',
    cwd: root,
    reference: transcript,
  })) as {
    tool: string
    turns: Array<{ inert: boolean, tool_calls?: Array<{ name: string, inert: boolean }> }>
    last_user_request: string
    last_assistant_action: string
  }

  assert.equal(result.tool, 'claude')
  assert.equal(result.last_user_request, 'Fix the fixture widget.')
  assert.match(result.last_assistant_action, /Updated widget\.ts/)
  assert.ok(result.turns.every(turn => turn.inert === true))
  assert.ok(result.turns.some(turn => turn.tool_calls?.some(call => call.name === 'Bash' && call.inert === true)))
})

test('vendored reader returns inert Cursor turns without replaying calls', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'dsh-resume-cursor-'))
  t.after(async () => { await rm(root, { recursive: true, force: true }) })
  const transcript = join(root, 'cursor-session.jsonl')
  const records = [
    { role: 'user', content: [{ type: 'text', text: '<user_query>Continue the Cursor refactor.</user_query>' }] },
    {
      role: 'assistant',
      content: [
        { type: 'text', text: 'Prepared the migration and stopped before applying it.' },
        { type: 'tool_call', call_id: 'cursor-call-1', name: 'write_file', arguments: { path: 'migration.ts' } },
      ],
    },
  ]
  await writeFile(transcript, `${records.map(record => JSON.stringify(record)).join('\n')}\n`)

  const result = JSON.parse(await runSessionReader({
    provider: 'cursor',
    action: 'show',
    cwd: root,
    reference: transcript,
  })) as {
    tool: string
    turns: Array<{ inert: boolean, tool_calls?: Array<{ name: string, inert: boolean }> }>
    last_user_request: string
    last_assistant_action: string
  }

  assert.equal(result.tool, 'cursor')
  assert.equal(result.last_user_request, 'Continue the Cursor refactor.')
  assert.match(result.last_assistant_action, /Prepared the migration/)
  assert.ok(result.turns.every(turn => turn.inert === true))
  assert.ok(result.turns.some(turn => turn.tool_calls?.some(call => call.name === 'write_file' && call.inert === true)))
})

test('vendored reader filters Codex instructions and returns inert calls and results', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'dsh-resume-codex-'))
  t.after(async () => { await rm(root, { recursive: true, force: true }) })
  const transcript = join(root, 'rollout-2026-08-20T00-00-00-11111111-1111-4111-8111-111111111111.jsonl')
  const records = [
    {
      timestamp: '2026-08-20T00:00:00.000Z',
      type: 'session_meta',
      payload: {
        id: '11111111-1111-4111-8111-111111111111',
        cwd: root,
        source: 'vscode',
        git: { branch: 'fixture' },
      },
    },
    {
      timestamp: '2026-08-20T00:00:01.000Z',
      type: 'response_item',
      payload: { type: 'message', role: 'user', content: [{ type: 'input_text', text: 'Continue the Codex fixture.' }] },
    },
    {
      timestamp: '2026-08-20T00:00:02.000Z',
      type: 'response_item',
      payload: { type: 'message', role: 'developer', content: [{ type: 'input_text', text: 'CODEX_PRIVATE_INSTRUCTION' }] },
    },
    {
      timestamp: '2026-08-20T00:00:03.000Z',
      type: 'response_item',
      payload: { type: 'reasoning', summary: [{ type: 'summary_text', text: 'CODEX_PRIVATE_REASONING' }] },
    },
    {
      timestamp: '2026-08-20T00:00:04.000Z',
      type: 'response_item',
      payload: { type: 'function_call', call_id: 'call-1', name: 'exec_command', arguments: '{"cmd":"pnpm test"}' },
    },
    {
      timestamp: '2026-08-20T00:00:05.000Z',
      type: 'response_item',
      payload: { type: 'function_call_output', call_id: 'call-1', output: 'all tests passed' },
    },
    {
      timestamp: '2026-08-20T00:00:06.000Z',
      type: 'response_item',
      payload: { type: 'message', role: 'assistant', content: [{ type: 'output_text', text: 'Stopped after the focused test.' }] },
    },
  ]
  await writeFile(transcript, `${records.map(record => JSON.stringify(record)).join('\n')}\n`)

  const raw = await runSessionReader({
    provider: 'codex',
    action: 'show',
    cwd: root,
    reference: transcript,
  })
  const result = JSON.parse(raw) as {
    tool: string
    source: string
    turns: Array<{
      inert: boolean
      tool_calls?: Array<{ name: string, inert: boolean }>
      tool_results?: Array<{ content: string, inert: boolean }>
    }>
    warnings: Array<{ code: string }>
    last_user_request: string
    last_assistant_action: string
  }

  assert.equal(result.tool, 'codex')
  assert.equal(result.source, 'codex-vscode')
  assert.equal(result.last_user_request, 'Continue the Codex fixture.')
  assert.equal(result.last_assistant_action, 'Stopped after the focused test.')
  assert.ok(result.turns.every(turn => turn.inert === true))
  assert.ok(result.turns.some(turn => turn.tool_calls?.some(call => call.name === 'exec_command' && call.inert === true)))
  assert.ok(result.turns.some(turn => turn.tool_results?.some(output => output.content.includes('all tests passed') && output.inert === true)))
  assert.ok(result.warnings.some(warning => warning.code === 'unsafe_records_skipped'))
  assert.doesNotMatch(raw, /CODEX_PRIVATE_INSTRUCTION|CODEX_PRIVATE_REASONING/)
})
