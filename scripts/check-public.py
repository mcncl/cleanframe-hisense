"""Check source paths, known private font blobs and common credential patterns.

This is a bounded release check, not a licence or complete secret audit.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess

from font_assets import ROOT


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


candidates = set(git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode().split('\0')) - {''}
objects = git('rev-list', '--objects', '--all').decode().splitlines()
findings = []
font_suffixes = {'.ttf', '.otf', '.woff', '.woff2', '.eot'}
private_suffixes = {'.p12', '.pem', '.key', '.csr', '.wgt'}


def forbidden(name):
    path = Path(name)
    return (name.startswith(('.local/', 'dist/', 'node_modules/', 'app/assets/private-fonts/',
                                    'explorations/', 'docs/research/', 'docs/articles/'))
            or path.suffix.lower() in private_suffixes
            or (path.name.startswith('PP') and path.suffix.lower() in font_suffixes)
            or path.name.startswith('.env.')
            or path.name in {'certificate-password.txt', 'profiles.xml', '.env', 'session.json', 'certs.bin.k', 'control-key'})


public_fonts = {'app/assets/manrope.woff2': 'e310b55a7fd9677f5e3555e6c6c4d064fa1f1d24393f0ddbe217cea12a8c432f'}
for record in json.loads((ROOT / 'app/assets/fonts/SOURCES.json').read_text()):
    if Path(record['file']).suffix.lower() in font_suffixes:
        public_fonts['app/assets/fonts/' + record['file']] = record['sha256']

for name in sorted(candidates):
    if forbidden(name):
        findings.append('Private/generated source path: ' + name)
    path = ROOT / name
    if path.is_symlink():
        findings.append('Symlink in public source: ' + name)
        continue
    if not path.is_file():
        continue
    if path.suffix.lower() in font_suffixes:
        if name not in public_fonts or hashlib.sha256(path.read_bytes()).hexdigest() != public_fonts[name]:
            findings.append('Unrecognised or changed public font: ' + name)
    try:
        content = path.read_text()
    except UnicodeError:
        continue
    # Print filenames only, so a failing check does not leak a matched credential.
    patterns = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                r'gh[pousr]_[A-Za-z0-9]{25,}', r'github_pat_[A-Za-z0-9_]{25,}',
                r'AKIA[A-Z0-9]{16}']
    if any(re.search(pattern, content) for pattern in patterns):
        findings.append('Credential pattern: ' + name)

object_ids = {line.split(' ', 1)[0] for line in objects}
for line in objects:
    parts = line.split(' ', 1)
    if len(parts) == 2 and forbidden(parts[1]):
        findings.append('Private/generated path in reachable Git history: ' + parts[1])
private_root = ROOT / '.local/research/font-candidates'
private_fonts = [p for p in private_root.rglob('*') if p.is_file() and p.name.startswith('PP') and p.suffix.lower() in font_suffixes]
for path in private_fonts:
    if git('hash-object', str(path)).decode().strip() in object_ids:
        findings.append('Known proprietary font bytes in Git history: ' + path.name)

for name in ['app/assets/fonts/geist/OFL.txt', 'app/assets/fonts/newsreader/OFL.txt', 'app/assets/manrope-OFL.txt']:
    if not (ROOT / name).is_file():
        findings.append('Missing public font licence: ' + name)

if findings:
    raise SystemExit('\n'.join(sorted(set(findings))[:20]) + '\nTotal findings: ' + str(len(set(findings))))
print('Public-source checks passed for ' + str(len(candidates)) + ' candidate files and reachable Git paths.')
print('Compared ' + str(len(private_fonts)) + ' local proprietary font files with reachable Git objects.')
if not private_fonts:
    print('No private fonts on this machine; known-font byte comparison was skipped.')
print('Also review third-party notices, full history, GitHub logs and release assets before publication.')
