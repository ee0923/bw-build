"""Publish checksum-verified final packages under the locked Bitwarden version."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time


def gh(*args, data=False):
    result = subprocess.check_output(['gh', *args], text=True)
    return json.loads(result) if data else result


def version(locks):
    clients = re.fullmatch(r'browser-v(\d+\.\d+\.\d+)', locks['clients']['ref'])
    android = re.fullmatch(r'v(\d+\.\d+\.\d+)-bwpm', locks['android']['ref'])
    if not clients or not android or clients[1] != android[1]:
        raise ValueError('Review release versions: locked client and Android versions differ')
    return clients[1]


def targets(choice):
    spec = importlib.util.spec_from_file_location('matrix', Path(__file__).with_name('build-matrix.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return ['bitwarden-' + t['id'] + '-' + t['arch'] for t in module.select(choice)['include']]


def verify_packages(folder):
    manifest = folder / 'SHA256SUMS'
    if manifest.is_symlink() or not manifest.is_file():
        raise ValueError('Missing package checksums')
    names = set()
    for line in manifest.read_text().splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  ([A-Za-z0-9][A-Za-z0-9._+-]*)', line)
        if not match:
            raise ValueError('Invalid package checksum entry')
        digest, name = match.groups()
        path = folder / name
        if (name in names or path.is_symlink() or not path.is_file()
                or not name.endswith(('.zip', '.tar.gz', '.dmg', '.apk'))):
            raise ValueError('Unexpected release package: ' + name)
        with path.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != digest:
                raise ValueError('Package checksum mismatch: ' + name)
        names.add(name)
    if not names or {p.name for p in folder.iterdir()} != names | {'SHA256SUMS'}:
        raise ValueError('Empty manifest or unexpected package files')
    return names


def publish():
    upstream = version(json.loads(Path('sources.lock.json').read_text()))
    target = os.environ['PACKAGE_ID']
    if target not in targets('all') or not re.fullmatch(r'[a-f0-9]{40}', os.environ['GITHUB_SHA']):
        raise ValueError('Invalid package identity or snapshot commit')
    source = Path('dist')
    names = verify_packages(source)
    output = Path('release-assets')
    output.mkdir()  # Refuse stale staged assets.
    for name in sorted(names):
        shutil.copyfile(source / name, output / name)
    checksum = 'SHA256SUMS-' + target
    shutil.copyfile(source / 'SHA256SUMS', output / checksum)
    tag = 'v' + upstream
    title = 'Bitwarden ' + upstream
    assets = [str(output / name) for name in sorted(names | {checksum})]
    # Matrix jobs can race to create the same version. Retry transient failures.
    for attempt in range(5):
        try:
            exists = subprocess.run(['gh', 'release', 'view', tag], stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL).returncode == 0
            if not exists:
                gh('release', 'create', tag, '--target', os.environ['GITHUB_SHA'], '--draft',
                   '--title', title, '--notes', 'Private Bitwarden packages. Android: Debug APK.')
            gh('release', 'upload', tag, *assets, '--clobber')
            gh('release', 'edit', tag, '--draft=false', '--title', title)
            print('https://github.com/' + os.environ['GH_REPO'] + '/releases/tag/' + tag)
            return
        except subprocess.CalledProcessError:
            if attempt == 4:
                raise
            time.sleep((attempt + 1) * 5)


if __name__ == '__main__':
    publish()
