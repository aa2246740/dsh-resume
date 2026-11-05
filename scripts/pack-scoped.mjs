import { execFileSync } from 'node:child_process'
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const source = fileURLToPath(new URL('..', import.meta.url))
const destination = resolve(process.argv[2] ?? '.')
const work = mkdtempSync(join(tmpdir(), 'dsh-resume-scoped-'))

try {
  const [original] = JSON.parse(execFileSync('npm', [
    'pack', '--ignore-scripts', '--json', '--pack-destination', work,
  ], { cwd: source, encoding: 'utf8' }))
  execFileSync('tar', ['-xzf', join(work, original.filename), '-C', work])
  const packageDir = join(work, 'package')
  const manifestFile = join(packageDir, 'package.json')
  const manifest = JSON.parse(readFileSync(manifestFile, 'utf8'))
  if (manifest.name !== 'dsh-resume') throw new Error('Unexpected source package name')
  manifest.name = '@aa2246740/dsh-resume'
  writeFileSync(manifestFile, `${JSON.stringify(manifest, null, 2)}\n`)
  const patchFile = join(packageDir, 'cordis.patch.yml')
  const patch = readFileSync(patchFile, 'utf8')
  const row = /^([ \t]*name:[ \t]*)dsh-resume[ \t]*$/gm
  if ([...patch.matchAll(row)].length !== 1) throw new Error('Expected one dsh-resume bundle row')
  writeFileSync(patchFile, patch.replace(row, '$1"@aa2246740/dsh-resume"'))
  const [packed] = JSON.parse(execFileSync('npm', [
    'pack', '--ignore-scripts', '--json', '--pack-destination', destination,
  ], { cwd: packageDir, encoding: 'utf8' }))
  console.log(join(destination, packed.filename))
} finally {
  rmSync(work, { recursive: true, force: true })
}
