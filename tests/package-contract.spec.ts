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
  devDependencies?: Record<string, string>
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

test('Harness peer ranges accept 0.1.7-rc.1 and 0.1.7-rc.2 and reject 0.1.7 alphas', () => {
  const skill = manifest.peerDependencies?.['@deepseek-ai/dsh-skill']
  const tools = manifest.peerDependencies?.['@deepseek-ai/dsh-tools']
  const range = '>=0.1.7-rc.1 <0.1.8'
  const boot = { includePrerelease: true }
  assert.equal(skill, range)
  assert.equal(tools, range)
  assert.equal(semver.satisfies('4.0.4', manifest.peerDependencies?.['@deepseek-ai/cordis']), true)
  for (const spec of [skill, tools]) {
    assert.ok(spec)
    assert.equal(semver.satisfies('0.1.7-rc.1', spec), true)
    assert.equal(semver.satisfies('0.1.7-rc.1', spec, boot), true)
    assert.equal(semver.satisfies('0.1.7-rc.2', spec), true)
    assert.equal(semver.satisfies('0.1.7-rc.2', spec, boot), true)
    assert.equal(semver.satisfies('0.1.5-rc.3', spec), false)
    assert.equal(semver.satisfies('0.1.5-rc.3', spec, boot), false)
    assert.equal(semver.satisfies('0.1.7-alpha.1', spec), false)
    assert.equal(semver.satisfies('0.1.7-alpha.1', spec, boot), false)
    assert.equal(semver.satisfies('0.1.7-alpha.2', spec), false)
    assert.equal(semver.satisfies('0.1.7-alpha.2', spec, boot), false)
    assert.equal(semver.satisfies('0.1.8.0', spec, boot), false)
  }
  assert.equal(semver.satisfies('0.1.7-rc.2', '^0.1.5-rc.3'), false)
  assert.equal(semver.satisfies('0.1.7-rc.1', '^0.1.5-rc.2'), false)
  assert.equal(semver.satisfies('0.1.7-alpha.2', '^0.1.5-rc.2', boot), true)
  assert.equal(semver.satisfies('0.1.8-alpha.1', range, boot), true)
})

test('dev dependencies track published Harness 0.1.7-rc.2', () => {
  const dev = manifest.devDependencies ?? {}
  assert.equal(dev['@deepseek-ai/cordis'], '4.0.4')
  const pinned = Object.entries(dev).filter(([name]) => name.startsWith('@deepseek-ai/dsh-'))
  assert.ok(pinned.length > 0)
  for (const [name, version] of pinned) {
    assert.equal(version, '0.1.7-rc.2', name)
  }
})
