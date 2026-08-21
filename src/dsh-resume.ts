import { existsSync } from 'node:fs'
import type { Context } from '@deepseek-ai/cordis'
import { defineTool } from '@deepseek-ai/dsh-tools'
import type {} from '@deepseek-ai/dsh-skill'
import {
  FOREIGN_SESSION_ACTIONS,
  FOREIGN_SESSION_PROVIDERS,
  GROK_SESSION_READER_PATH,
  runSessionReader,
  SESSION_READER_PATH,
  slashReferenceFromSession,
} from './reader.ts'
import { RESUME_SKILL_SPECS, skillRegistration } from './skills.ts'

export const name = 'dsh-resume'
export const inject = ['tools', 'skills']

const JSON_TEXT_OUTPUT = {
  schema: { type: 'string' as const },
  render: (_args: unknown, value: string) => [{ type: 'text' as const, text: value }],
}

/** Register one read-only reader tool and five user-only slash skills. */
export function apply(ctx: Context): void {
  if (!existsSync(SESSION_READER_PATH)) {
    throw new Error(`dsh-resume: missing bundled reader at ${SESSION_READER_PATH}`)
  }
  if (!existsSync(GROK_SESSION_READER_PATH)) {
    throw new Error(`dsh-resume: missing pinned Grok reader at ${GROK_SESSION_READER_PATH}`)
  }

  console.log('[dsh-resume] loaded')
  ctx.tools.register(defineTool({
    name: 'foreign_session_read',
    description: 'Read Codex, Claude Code, Cursor, Grok, or Pi local session history into a Grok-compatible inert JSON schema. Use only after an explicit resume slash skill or explicit user request. Discovery is scoped to the current DSH working directory; an explicit native ID or path is supported. The tool is read-only and never executes recovered calls.',
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
      const action = args.action ?? 'show'
      const inferred = args.reference?.trim()
        || (action === 'show'
          ? slashReferenceFromSession(exec.agent?.session.events, args.provider)
          : undefined)
      return await runSessionReader({
        provider: args.provider,
        action,
        cwd,
        ...inferred ? { reference: inferred } : {},
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

export {
  buildReaderArgs,
  GROK_SESSION_READER_PATH,
  runSessionReader,
  SESSION_READER_PATH,
  slashReferenceFromSession,
  slashReferenceFromUserText,
} from './reader.ts'
export { RESUME_SKILL_SPECS, resumeSkillContent, skillRegistration } from './skills.ts'
