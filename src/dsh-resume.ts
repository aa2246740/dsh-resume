import { existsSync } from 'node:fs'
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import type {} from '@deepseek-ai/dsh-skill'
import {
  FOREIGN_SESSION_ACTIONS,
  FOREIGN_SESSION_PROVIDERS,
  runSessionReader,
  SESSION_READER_PATH,
} from './reader.ts'
import { RESUME_SKILL_SPECS, skillRegistration } from './skills.ts'

export const name = 'dsh-resume'
export const inject = ['tools', 'skills']

const JSON_TEXT_OUTPUT = {
  schema: { type: 'string' as const },
  render: (_args: unknown, value: string) => [{ type: 'text' as const, text: value }],
}

/** Register one read-only reader tool and three user-only slash skills. */
export function apply(ctx: Context): void {
  if (!existsSync(SESSION_READER_PATH)) {
    throw new Error(`dsh-resume: missing bundled reader at ${SESSION_READER_PATH}`)
  }

  console.log('[dsh-resume] loaded')
  ctx.tools.register(defineTool({
    name: 'foreign_session_read',
    description: 'Read Codex, Claude Code, or Cursor local session history into the Grok-compatible inert JSON schema. Use only after an explicit resume slash skill or explicit user request. Discovery is scoped to the current DSH working directory; an explicit native ID or path is supported. The tool is read-only and never executes recovered calls.',
    parameters: {
      provider: {
        type: 'string',
        required: true,
        enum: [...FOREIGN_SESSION_PROVIDERS],
        description: 'Foreign coding agent that owns the local session store.',
      },
      action: {
        type: 'string',
        enum: [...FOREIGN_SESSION_ACTIONS],
        default: 'show',
        description: 'show resolves one session; list returns current-workspace candidates.',
      },
      reference: {
        type: 'string',
        description: 'Optional native session ID, transcript/store path, or title substring. Omit for latest.',
      },
      withinMinutes: {
        type: 'integer',
        description: 'Optional non-negative discovery recency window in minutes. Omit for all matching sessions.',
      },
      maxToolChars: {
        type: 'integer',
        default: 300,
        description: 'Maximum recovered characters for each inert foreign tool call or result; accepted range is 1-10000.',
      },
    },
    output: JSON_TEXT_OUTPUT,
    isConcurrencySafe: () => true,
    async execute(args, exec) {
      const cwd = exec.agent?.session.header.cwd ?? process.cwd()
      return await runSessionReader({
        provider: args.provider,
        action: args.action ?? 'show',
        cwd,
        ...args.reference === undefined ? {} : { reference: args.reference },
        ...args.withinMinutes === undefined ? {} : { withinMinutes: args.withinMinutes },
        ...args.maxToolChars === undefined ? {} : { maxToolChars: args.maxToolChars },
        signal: exec.signal,
      })
    },
    presentCall(args) {
      const action = args.action ?? 'show'
      return {
        card: 'generic',
        title: action === 'list'
          ? `List ${args.provider} sessions`
          : `Resume ${args.provider} session`,
        kind: 'read',
        rawInput: args.reference ?? 'latest',
      }
    },
  }))

  for (const spec of RESUME_SKILL_SPECS) {
    ctx.skills.register(skillRegistration(spec))
  }
}

export { buildReaderArgs, runSessionReader, SESSION_READER_PATH } from './reader.ts'
export { RESUME_SKILL_SPECS, resumeSkillContent, skillRegistration } from './skills.ts'
