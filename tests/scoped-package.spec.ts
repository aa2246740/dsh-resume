import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync } from 'node:fs'
import { createRequire } from 'node:module'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import test from 'node:test'
import { fileURLToPath } from 'node:url'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')

test('scoped release resolves the package named by its bundle patch in a clean install', () => {
  const work = mkdtempSync(join(tmpdir(), 'dsh-resume-package-test-'))
  try {
    const archive = execFileSync('node', [join(root, 'scripts/pack-scoped.mjs'), work], {
      cwd: root, encoding: 'utf8',
    }).trim()
    const patch = execFileSync('tar', ['-xOf', archive, 'package/cordis.patch.yml'], { encoding: 'utf8' })
    const packageName = /^[ \t]+name:[ \t]*"?([^"\s]+)"?[ \t]*$/m.exec(patch)?.[1]
    assert.equal(packageName, '@aa2246740/dsh-resume')
    assert.match(patch, /^[ \t]+-[ \t]+id:[ \t]+dsh-resume[ \t]*$/m)
    assert.match(readFileSync(join(root, 'cordis.patch.yml'), 'utf8'), /^[ \t]+name:[ \t]+dsh-resume[ \t]*$/m)

    const profile = join(work, 'profile')
    execFileSync('npm', [
      'install', '--prefix', profile, '--ignore-scripts', '--no-audit', '--no-fund',
      '--no-package-lock', '--legacy-peer-deps', archive,
    ], { stdio: 'pipe' })
    const requireFromProfile = createRequire(join(profile, 'package.json'))
    assert.match(requireFromProfile.resolve(packageName), /dsh-resume\.js$/)
    const manifest = JSON.parse(readFileSync(requireFromProfile.resolve(`${packageName}/package.json`), 'utf8'))
    assert.equal(manifest.name, packageName)
  } finally {
    rmSync(work, { recursive: true, force: true })
  }
})
