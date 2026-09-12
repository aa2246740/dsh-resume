import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const manifest = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')) as {
  main?: string
  files?: string[]
  scripts?: Record<string, string>
  keywords?: string[]
  dsh?: { bundle?: { patch?: string } }
}

test('stock dsh plugin add can mount this package as a bundle', () => {
  assert.equal(manifest.dsh?.bundle?.patch, './cordis.patch.yml')
  assert.equal(manifest.main, 'lib/dsh-resume.js')
  assert.equal(manifest.scripts?.prepare, undefined)
  assert.ok(existsSync(join(root, 'lib', 'dsh-resume.js')))
  assert.ok(existsSync(join(root, 'cordis.patch.yml')))
  assert.ok(existsSync(join(root, 'resources', 'dsh_session_reader.py')))
  assert.ok(existsSync(join(root, 'resources', 'session_reader.py')))
  assert.ok(manifest.files?.includes('lib/*.js'))
  assert.ok(manifest.files?.includes('cordis.patch.yml'))
  assert.ok(manifest.keywords?.includes('dsh-plugin'))
})
