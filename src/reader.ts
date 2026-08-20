import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

export const FOREIGN_SESSION_PROVIDERS = ['claude', 'codex', 'cursor'] as const
export type ForeignSessionProvider = typeof FOREIGN_SESSION_PROVIDERS[number]

export const FOREIGN_SESSION_ACTIONS = ['show', 'list'] as const
export type ForeignSessionAction = typeof FOREIGN_SESSION_ACTIONS[number]

const DEFAULT_MAX_TOOL_CHARS = 300
const DEFAULT_MAX_OUTPUT_BYTES = 8 * 1024 * 1024
const MAX_STDERR_BYTES = 256 * 1024

const PLUGIN_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
export const SESSION_READER_PATH = join(PLUGIN_ROOT, 'resources', 'session_reader.py')

interface PythonCommand {
  readonly command: string
  readonly prefix: readonly string[]
}

export interface ReaderRequest {
  readonly provider: ForeignSessionProvider
  readonly action: ForeignSessionAction
  readonly cwd: string
  readonly reference?: string
  readonly withinMinutes?: number
  readonly maxToolChars?: number
  readonly signal?: AbortSignal
  readonly readerPath?: string
  readonly maxOutputBytes?: number
}

interface ProcessResult {
  readonly code: number | null
  readonly stdout: string
  readonly stderr: string
}

/** Build the fixed, shell-free reader argv used by the DSH tool. */
export function buildReaderArgs(request: ReaderRequest): string[] {
  assertProvider(request.provider)
  assertAction(request.action)
  const cwd = resolve(request.cwd)
  const withinMinutes = request.withinMinutes ?? 0
  const maxToolChars = request.maxToolChars ?? DEFAULT_MAX_TOOL_CHARS
  assertIntegerInRange('withinMinutes', withinMinutes, 0, Number.MAX_SAFE_INTEGER)
  assertIntegerInRange('maxToolChars', maxToolChars, 1, 10_000)

  const reference = request.reference?.trim()
  if (request.action === 'list' && reference) {
    throw new TypeError('foreign session list does not accept a reference')
  }

  const args = [
    request.provider,
    request.action,
    '--cwd',
    cwd,
    '--within-min',
    String(withinMinutes),
    '--max-tool-chars',
    String(maxToolChars),
    // Grok's resume skills consume the reader's structured schema. Keep the
    // DSH adapter on that exact path instead of the lossy human renderer.
    '--json',
  ]
  // `--` keeps a reference beginning with a dash inert instead of turning it
  // into a Python argparse option.
  if (request.action === 'show' && reference) args.push('--', reference)
  return args
}

/**
 * Run the vendored Grok reader as a bounded, read-only child process.
 * Exit 2 is returned as ordinary text because it carries disambiguation
 * candidates the agent must show to the user.
 */
export async function runSessionReader(request: ReaderRequest): Promise<string> {
  const readerPath = request.readerPath ?? SESSION_READER_PATH
  if (!existsSync(readerPath)) {
    throw new Error(`foreign session reader is missing at ${readerPath}`)
  }
  request.signal?.throwIfAborted()
  const args = [readerPath, ...buildReaderArgs(request)]
  const commands = pythonCommands()
  let missing: unknown

  for (const candidate of commands) {
    try {
      const result = await spawnBounded(
        candidate.command,
        [...candidate.prefix, ...args],
        request.signal,
        request.maxOutputBytes ?? DEFAULT_MAX_OUTPUT_BYTES,
      )
      if (result.code === 0) return result.stdout

      const detail = (result.stderr || result.stdout).trim()
      if (result.code === 2) {
        return [
          'FOREIGN_SESSION_LOOKUP_NEEDS_INPUT',
          'No foreign session was resumed.',
          detail || 'The reader could not resolve a unique session.',
        ].join('\n')
      }
      return [
        'FOREIGN_SESSION_READER_FAILED',
        `Provider: ${request.provider}`,
        `Working directory: ${resolve(request.cwd)}`,
        detail || `Reader exited with code ${String(result.code)}.`,
      ].join('\n')
    } catch (error: unknown) {
      if (isMissingExecutable(error)) {
        missing = error
        continue
      }
      throw error
    }
  }

  throw new Error(
    'No supported Python 3 launcher was found (tried python3/python, or py -3 on Windows).',
    { cause: missing },
  )
}

function pythonCommands(): readonly PythonCommand[] {
  return process.platform === 'win32'
    ? [
        { command: 'py', prefix: ['-3'] },
        { command: 'python3', prefix: [] },
        { command: 'python', prefix: [] },
      ]
    : [
        { command: 'python3', prefix: [] },
        { command: 'python', prefix: [] },
      ]
}

function spawnBounded(
  command: string,
  args: readonly string[],
  signal: AbortSignal | undefined,
  maxOutputBytes: number,
): Promise<ProcessResult> {
  assertIntegerInRange('maxOutputBytes', maxOutputBytes, 1, 64 * 1024 * 1024)
  return new Promise((resolvePromise, rejectPromise) => {
    const child = spawn(command, [...args], {
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    })
    const stdout: Buffer[] = []
    const stderr: Buffer[] = []
    let stdoutBytes = 0
    let stderrBytes = 0
    let settled = false
    let limitError: Error | undefined

    const cleanup = (): void => {
      signal?.removeEventListener('abort', onAbort)
    }
    const settleReject = (error: unknown): void => {
      if (settled) return
      settled = true
      cleanup()
      rejectPromise(error)
    }
    const onAbort = (): void => {
      child.kill('SIGTERM')
      settleReject(abortError(signal?.reason))
    }
    const append = (target: Buffer[], chunk: Buffer, stream: 'stdout' | 'stderr'): void => {
      if (settled || limitError) return
      if (stream === 'stdout') stdoutBytes += chunk.length
      else stderrBytes += chunk.length
      const limit = stream === 'stdout' ? maxOutputBytes : MAX_STDERR_BYTES
      const size = stream === 'stdout' ? stdoutBytes : stderrBytes
      if (size > limit) {
        limitError = new Error(`foreign session reader ${stream} exceeded ${limit} bytes`)
        child.kill('SIGTERM')
        return
      }
      target.push(chunk)
    }

    child.stdout.on('data', (chunk: Buffer) => { append(stdout, chunk, 'stdout') })
    child.stderr.on('data', (chunk: Buffer) => { append(stderr, chunk, 'stderr') })
    child.once('error', settleReject)
    child.once('close', (code) => {
      if (settled) return
      if (limitError) {
        settleReject(limitError)
        return
      }
      settled = true
      cleanup()
      resolvePromise({
        code,
        stdout: Buffer.concat(stdout).toString('utf8'),
        stderr: Buffer.concat(stderr).toString('utf8'),
      })
    })

    if (signal?.aborted) onAbort()
    else signal?.addEventListener('abort', onAbort, { once: true })
  })
}

function assertProvider(value: string): asserts value is ForeignSessionProvider {
  if (!FOREIGN_SESSION_PROVIDERS.includes(value as ForeignSessionProvider)) {
    throw new TypeError(`unsupported foreign session provider: ${value}`)
  }
}

function assertAction(value: string): asserts value is ForeignSessionAction {
  if (!FOREIGN_SESSION_ACTIONS.includes(value as ForeignSessionAction)) {
    throw new TypeError(`unsupported foreign session action: ${value}`)
  }
}

function assertIntegerInRange(name: string, value: number, minimum: number, maximum: number): void {
  if (!Number.isSafeInteger(value) || value < minimum || value > maximum) {
    throw new TypeError(`${name} must be an integer between ${minimum} and ${maximum}`)
  }
}

function isMissingExecutable(error: unknown): boolean {
  return typeof error === 'object' && error !== null && (error as { code?: unknown }).code === 'ENOENT'
}

function abortError(cause: unknown): Error {
  const error = new Error('foreign session reader aborted', { cause })
  error.name = 'AbortError'
  return error
}
