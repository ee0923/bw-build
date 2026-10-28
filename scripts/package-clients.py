"""Check private-client output before packaging; upload only allowlisted final artifacts."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile


def validate_bundle(built, target, server):
    if not built.is_dir() or not any(built.iterdir()):
        raise ValueError('Missing client build output')
    if not any(server.encode() in p.read_bytes() for p in built.rglob('*.js')):
        raise ValueError('Private default server is absent from the compiled client')
    if target == 'browser':
        manifest = json.loads((built / 'manifest.json').read_text())
        if manifest.get('version') != '2026.10.0' or 'update_url' in manifest or manifest.get('homepage_url'):
            raise ValueError('Unexpected extension version or official update/homepage URL')
        if os.environ.get('BW_BUILD_BROWSER') in ('chrome', 'edge') and (
            manifest.get('manifest_version') != 3 or manifest.get('version_name') != '2026.10.0-private'
        ):
            raise ValueError('Unexpected Chromium manifest identity')
        csp = manifest.get('content_security_policy', '')
        if isinstance(csp, dict):
            csp = csp.get('extension_pages', '')
        directives = {p[0]: set(p[1:]) for s in csp.split(';') if (p := s.split())}
        if directives.get('connect-src') != {"'self'", 'blob:', 'data:', 'https:', 'http:', 'wss:', 'ws:'}:
            raise ValueError('Extension network policy does not support custom servers')
        if manifest.get('manifest_version') == 3 and 'declarativeNetRequestWithHostAccess' not in manifest.get('permissions', []):
            raise ValueError('Extension is missing the official destination blocker')


def main():
    target = os.environ['BW_BUILD_TARGET']
    dist = Path('dist'); dist.mkdir(exist_ok=True)
    if '--desktop-output' in sys.argv:
        artifacts = [p for p in Path('source/apps/desktop/dist').iterdir()
                     if p.is_file() and (p.name.endswith('.tar.gz') or p.suffix in ('.zip', '.dmg'))]
        if not artifacts:
            raise ValueError('Desktop packaging produced no archive')
        for path in artifacts:
            shutil.copy2(path, dist / path.name)
        return
    spec = importlib.util.spec_from_file_location('defaults', Path(__file__).with_name('default-server.py'))
    policy = importlib.util.module_from_spec(spec); spec.loader.exec_module(policy)
    server = policy.validate(os.environ.get('BW_DEFAULT_SERVER_URL', ''))
    app = {'browser': 'browser', 'web': 'web', 'cli': 'cli', 'desktop': 'desktop'}[target]
    built = Path('source/apps') / app / 'build'
    validate_bundle(built, target, server)
    if target == 'desktop':
        return  # A JavaScript directory alone is not a desktop application.
    name = 'browser-' + os.environ['BW_BUILD_BROWSER'] if target == 'browser' else target
    with zipfile.ZipFile(dist / ('bitwarden-' + name + '-private.zip'), 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(built.rglob('*')):
            if path.is_file():
                archive.write(path, path.relative_to(built))


if __name__ == '__main__':
    main()
