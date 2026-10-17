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
  engines?: Record<string, string>
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

test('Harness peer and engines.dsh ranges accept 0.2.1-rc.* and stable 0.2.1 and reject alphas and 0.2.0-rc.2', () => {
  const skill = manifest.peerDependencies?.['@deepseek-ai/dsh-skill']
  const tools = manifest.peerDependencies?.['@deepseek-ai/dsh-tools']
  const enginesDsh = manifest.engines?.dsh
  const range = '>=0.2.1-rc.1 <0.2.2'
  const previous = '>=0.2.0-rc.1 <0.2.1'
  const boot = { includePrerelease: true }
  assert.equal(skill, range)
  assert.equal(tools, range)
  assert.equal(enginesDsh, range)
  assert.equal(semver.satisfies('4.0.4', manifest.peerDependencies?.['@deepseek-ai/cordis']), true)
  for (const spec of [skill, tools, enginesDsh]) {
    assert.ok(spec)
    assert.equal(semver.satisfies('0.2.1-rc.1', spec), true)
    assert.equal(semver.satisfies('0.2.1-rc.1', spec, boot), true)
    assert.equal(semver.satisfies('0.2.1-rc.2', spec), true)
    assert.equal(semver.satisfies('0.2.1-rc.2', spec, boot), true)
    assert.equal(semver.satisfies('0.2.1', spec), true)
    assert.equal(semver.satisfies('0.2.1', spec, boot), true)
    assert.equal(semver.satisfies('0.2.1-alpha.5', spec), false)
    assert.equal(semver.satisfies('0.2.1-alpha.5', spec, boot), false)
    assert.equal(semver.satisfies('0.2.0-rc.2', spec), false)
    assert.equal(semver.satisfies('0.2.0-rc.2', spec, boot), false)
    assert.equal(semver.satisfies('0.2.0', spec), false)
    assert.equal(semver.satisfies('0.2.0', spec, boot), false)
    assert.equal(semver.satisfies('0.2.2', spec), false)
    assert.equal(semver.satisfies('0.2.2', spec, boot), false)
    // Default semver rejects 0.2.1-rc.* against the old <0.2.1 peers.
    // includePrerelease still accepts them because they are below 0.2.1.
    assert.equal(semver.satisfies('0.2.1-rc.2', previous), false)
    assert.equal(semver.satisfies('0.2.1-rc.2', previous, boot), true)
  }
})

test('dev dependencies track published Harness 0.2.1-rc.2', () => {
  const dev = manifest.devDependencies ?? {}
  assert.equal(dev['@deepseek-ai/cordis'], '4.0.5')
  assert.equal(dev['@deepseek-ai/dsh-invariants'], undefined)
  const pinned = Object.entries(dev).filter(([name]) => name.startsWith('@deepseek-ai/dsh-'))
  assert.ok(pinned.length > 0)
  for (const [name, version] of pinned) {
    assert.equal(version, '0.2.1-rc.2', name)
  }
})
