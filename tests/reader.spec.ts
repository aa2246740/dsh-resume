import assert from 'node:assert/strict'
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import test from 'node:test'
import {
  buildReaderArgs,
  runSessionReader,
  slashReferenceFromSession,
  slashReferenceFromUserText,
} from '../src/reader.ts'

test('slashReferenceFromUserText keeps latest empty and checkout intact', () => {
  assert.equal(slashReferenceFromUserText('/resume-claude latest', 'claude'), undefined)
  assert.equal(slashReferenceFromUserText('/resume-claude', 'claude'), undefined)
  assert.equal(slashReferenceFromUserText('/resume-claude checkout', 'claude'), 'checkout')
  assert.equal(slashReferenceFromUserText('please /resume-claude checkout now', 'claude'), 'checkout')
})

test('slashReferenceFromSession reads the triggering user message', () => {
  const events = [
    { type: 'user/message', data: { content: [{ type: 'text', text: '/resume-claude checkout' }] } },
    { type: 'user/message', data: { content: [{ type: 'text', text: '<skill_content name="resume-claude">' }] } },
  ]
  assert.equal(slashReferenceFromSession(events, 'claude'), 'checkout')
})

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

test('Grok adapter reads only visible updates and keeps calls, results, and plans inert', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'dsh-resume-grok-'))
  t.after(async () => { await rm(root, { recursive: true, force: true }) })
  const sessionDir = join(root, '22222222-2222-4222-8222-222222222222')
  await mkdir(sessionDir)
  await writeFile(join(sessionDir, 'summary.json'), JSON.stringify({
    info: { id: '22222222-2222-4222-8222-222222222222', cwd: root },
    generated_title: 'Grok fixture session',
    created_at: '2026-08-20T01:00:00.000Z',
    last_active_at: '2026-08-20T01:05:00.000Z',
    current_model_id: 'grok-code-fast',
    git_root_dir: root,
    head_commit: 'fixture-commit',
    chat_format_version: 1,
  }))
  const update = (sessionUpdate: string, value: Record<string, unknown>) => ({
    method: 'session/update',
    timestamp: '2026-08-20T01:00:00.000Z',
    params: {
      sessionId: '22222222-2222-4222-8222-222222222222',
      update: { sessionUpdate, ...value },
    },
  })
  const records = [
    update('user_message_chunk', { content: 'Continue the Grok fixture.' }),
    update('agent_thought_chunk', { content: 'GROK_PRIVATE_THOUGHT' }),
    update('agent_message_chunk', { content: 'Prepared the visible Grok change.' }),
    update('tool_call', {
      toolCallId: 'grok-call-1',
      title: 'Run tests',
      rawInput: { command: 'pnpm test' },
      _meta: { 'x.ai/tool': { name: 'shell' } },
    }),
    update('tool_call_update', {
      toolCallId: 'grok-call-1',
      status: 'completed',
      content: [{ type: 'content', content: { type: 'text', text: 'focused tests passed' } }],
      rawOutput: { output: 'fallback output' },
    }),
    update('plan', {
      entries: [{ content: 'Publish after verification', status: 'pending', priority: 'high' }],
    }),
    update('hook_execution', { event_name: 'after-turn', prompt: 'GROK_PRIVATE_HOOK' }),
    update('turn_completed', { stop_reason: 'end_turn' }),
  ]
  await writeFile(
    join(sessionDir, 'updates.jsonl'),
    `${records.map(record => JSON.stringify(record)).join('\n')}\n`,
  )

  const raw = await runSessionReader({
    provider: 'grok',
    action: 'show',
    cwd: root,
    reference: sessionDir,
  })
  const result = JSON.parse(raw) as {
    tool: string
    turns: Array<{
      inert: boolean
      tool_calls?: Array<{ name: string, inert: boolean }>
      tool_results?: Array<{ content: string, inert: boolean }>
    }>
    plan: Array<{ content: string, inert: boolean }>
    warnings: Array<{ code: string }>
    last_user_request: string
  }

  assert.equal(result.tool, 'grok')
  assert.equal(result.last_user_request, 'Continue the Grok fixture.')
  assert.ok(result.turns.every(turn => turn.inert === true))
  assert.ok(result.turns.some(turn => turn.tool_calls?.some(call => call.name === 'shell' && call.inert === true)))
  assert.ok(result.turns.some(turn => turn.tool_results?.some(output => output.content.includes('focused tests passed') && output.inert === true)))
  assert.deepEqual(result.plan, [{ content: 'Publish after verification', status: 'pending', inert: true }])
  assert.ok(result.warnings.some(warning => warning.code === 'hidden_reasoning_skipped'))
  assert.ok(result.warnings.some(warning => warning.code === 'hook_records_skipped'))
  assert.doesNotMatch(raw, /GROK_PRIVATE_THOUGHT|GROK_PRIVATE_HOOK/)
})

test('Pi adapter follows the active branch and excludes thinking and extension records', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'dsh-resume-pi-'))
  t.after(async () => { await rm(root, { recursive: true, force: true }) })
  const transcript = join(root, '2026-08-20T02-00-00-000Z_33333333-3333-4333-8333-333333333333.jsonl')
  const records = [
    {
      type: 'session',
      version: 3,
      id: '33333333-3333-4333-8333-333333333333',
      timestamp: '2026-08-20T02:00:00.000Z',
      cwd: root,
    },
    {
      type: 'message',
      id: 'pi-user-root',
      parentId: null,
      timestamp: '2026-08-20T02:00:01.000Z',
      message: { role: 'user', content: [{ type: 'text', text: 'Continue the Pi fixture.' }] },
    },
    {
      type: 'message',
      id: 'pi-abandoned',
      parentId: 'pi-user-root',
      timestamp: '2026-08-20T02:00:02.000Z',
      message: { role: 'assistant', content: [{ type: 'text', text: 'PI_ABANDONED_BRANCH' }] },
    },
    {
      type: 'message',
      id: 'pi-assistant-active',
      parentId: 'pi-user-root',
      timestamp: '2026-08-20T02:00:03.000Z',
      message: {
        role: 'assistant',
        model: 'pi-fixture-model',
        content: [
          { type: 'thinking', thinking: 'PI_PRIVATE_THINKING' },
          { type: 'text', text: 'Prepared the active Pi branch.' },
          { type: 'toolCall', id: 'pi-call-1', name: 'bash', arguments: { command: 'pnpm test' } },
        ],
      },
    },
    {
      type: 'message',
      id: 'pi-tool-result',
      parentId: 'pi-assistant-active',
      timestamp: '2026-08-20T02:00:04.000Z',
      message: {
        role: 'toolResult',
        toolCallId: 'pi-call-1',
        toolName: 'bash',
        isError: false,
        content: [{ type: 'text', text: 'Pi focused tests passed' }],
      },
    },
    {
      type: 'custom',
      id: 'pi-custom',
      parentId: 'pi-tool-result',
      timestamp: '2026-08-20T02:00:05.000Z',
      customType: 'fixture-extension',
      data: 'PI_PRIVATE_EXTENSION_RECORD',
    },
    {
      type: 'message',
      id: 'pi-assistant-final',
      parentId: 'pi-custom',
      timestamp: '2026-08-20T02:00:06.000Z',
      message: { role: 'assistant', content: [{ type: 'text', text: 'Stopped after the Pi focused test.' }] },
    },
  ]
  await writeFile(transcript, `${records.map(record => JSON.stringify(record)).join('\n')}\n`)

  const raw = await runSessionReader({
    provider: 'pi',
    action: 'show',
    cwd: root,
    reference: transcript,
  })
  const result = JSON.parse(raw) as {
    tool: string
    active_leaf_id: string
    turns: Array<{
      inert: boolean
      tool_calls?: Array<{ name: string, inert: boolean }>
      tool_results?: Array<{ content: string, inert: boolean }>
    }>
    warnings: Array<{ code: string }>
    last_user_request: string
    last_assistant_action: string
  }

  assert.equal(result.tool, 'pi')
  assert.equal(result.active_leaf_id, 'pi-assistant-final')
  assert.equal(result.last_user_request, 'Continue the Pi fixture.')
  assert.equal(result.last_assistant_action, 'Stopped after the Pi focused test.')
  assert.ok(result.turns.every(turn => turn.inert === true))
  assert.ok(result.turns.some(turn => turn.tool_calls?.some(call => call.name === 'bash' && call.inert === true)))
  assert.ok(result.turns.some(turn => turn.tool_results?.some(output => output.content.includes('Pi focused tests passed') && output.inert === true)))
  assert.ok(result.warnings.some(warning => warning.code === 'inactive_branch_entries_skipped'))
  assert.ok(result.warnings.some(warning => warning.code === 'hidden_reasoning_skipped'))
  assert.ok(result.warnings.some(warning => warning.code === 'extension_records_skipped'))
  assert.doesNotMatch(raw, /PI_ABANDONED_BRANCH|PI_PRIVATE_THINKING|PI_PRIVATE_EXTENSION_RECORD/)
})

test('Grok and Pi automatic discovery stays scoped to the current workspace', async (t) => {
  const root = await mkdtemp(join(tmpdir(), 'dsh-resume-discovery-'))
  const previousGrokHome = process.env.GROK_HOME
  const previousPiSessionDir = process.env.PI_CODING_AGENT_SESSION_DIR
  t.after(async () => {
    if (previousGrokHome === undefined) delete process.env.GROK_HOME
    else process.env.GROK_HOME = previousGrokHome
    if (previousPiSessionDir === undefined) delete process.env.PI_CODING_AGENT_SESSION_DIR
    else process.env.PI_CODING_AGENT_SESSION_DIR = previousPiSessionDir
    await rm(root, { recursive: true, force: true })
  })

  const grokHome = join(root, 'grok-home')
  const grokSession = join(
    grokHome,
    'sessions',
    encodeURIComponent(resolve(root)),
    '44444444-4444-4444-8444-444444444444',
  )
  await mkdir(grokSession, { recursive: true })
  await writeFile(join(grokSession, 'summary.json'), JSON.stringify({
    info: { id: '44444444-4444-4444-8444-444444444444', cwd: resolve(root) },
    generated_title: 'Discoverable Grok fixture',
    last_active_at: '2026-08-20T03:00:00.000Z',
  }))
  await writeFile(
    join(grokSession, 'updates.jsonl'),
    `${JSON.stringify({ sessionUpdate: 'user_message_chunk', content: 'Grok discovery fixture.' })}\n`,
  )

  const piSessionDir = join(root, 'pi-sessions')
  await mkdir(piSessionDir)
  const piSession = (id: string, cwd: string) => [
    { type: 'session', version: 3, id, timestamp: '2026-08-20T03:00:00.000Z', cwd },
    {
      type: 'message',
      id: `${id}-user`,
      parentId: null,
      timestamp: '2026-08-20T03:00:01.000Z',
      message: { role: 'user', content: [{ type: 'text', text: 'Pi discovery fixture.' }] },
    },
  ]
  await writeFile(
    join(piSessionDir, 'matching.jsonl'),
    `${piSession('55555555-5555-4555-8555-555555555555', resolve(root)).map(record => JSON.stringify(record)).join('\n')}\n`,
  )
  await writeFile(
    join(piSessionDir, 'other-workspace.jsonl'),
    `${piSession('66666666-6666-4666-8666-666666666666', join(root, 'other')).map(record => JSON.stringify(record)).join('\n')}\n`,
  )

  process.env.GROK_HOME = grokHome
  process.env.PI_CODING_AGENT_SESSION_DIR = piSessionDir
  const grokList = JSON.parse(await runSessionReader({
    provider: 'grok',
    action: 'list',
    cwd: root,
  })) as { sessions: Array<{ session_id: string, cwd: string }> }
  const piList = JSON.parse(await runSessionReader({
    provider: 'pi',
    action: 'list',
    cwd: root,
  })) as { sessions: Array<{ session_id: string, cwd: string }> }

  assert.deepEqual(grokList.sessions.map(session => session.session_id), [
    '44444444-4444-4444-8444-444444444444',
  ])
  assert.deepEqual(piList.sessions.map(session => session.session_id), [
    '55555555-5555-4555-8555-555555555555',
  ])
  assert.ok(grokList.sessions.every(session => session.cwd === resolve(root)))
  assert.ok(piList.sessions.every(session => session.cwd === resolve(root)))
})
