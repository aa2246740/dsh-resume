import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'
import semver from 'semver'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const manifest = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')) as {
  main?: string
  files?: string[]
  scripts?: Record<string, string>
  keywords?: string[]
  peerDependencies?: Record<string, string>
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

test('Harness peer ranges accept 0.1.5-rc.3 and reject the old prerelease caret', () => {
  const skill = manifest.peerDependencies?.['@deepseek-ai/dsh-skill']
  const tools = manifest.peerDependencies?.['@deepseek-ai/dsh-tools']
  assert.equal(skill, '^0.1.5-rc.2')
  assert.equal(tools, '^0.1.5-rc.2')
  assert.equal(semver.satisfies('0.1.5-rc.3', '^0.1.2-rc.1'), false)
  assert.equal(semver.satisfies('0.1.5-rc.3', skill), true)
  assert.equal(semver.satisfies('0.1.5-rc.3', tools), true)
  assert.equal(semver.satisfies('0.1.7-alpha.2', skill), false)
  assert.equal(semver.satisfies('0.1.7-alpha.2', tools), false)
})
