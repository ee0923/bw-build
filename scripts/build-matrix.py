"""Select only supported client/platform combinations for one Actions workflow."""
import json
import sys

TARGETS = [
    dict(id='browser-' + browser, app='clients', target='browser', browser=browser,
         platform='linux', arch='x64', runner='ubuntu-24.04', timeout=90,
         secret='BITWARDEN_CUSTOMIZE_SCRIPT')
    for browser in ('chrome', 'edge', 'firefox')
] + [
    dict(id=target, app='clients', target=target, browser='', platform='linux',
         arch='x64', runner='ubuntu-24.04', timeout=90,
         secret='BITWARDEN_CUSTOMIZE_SCRIPT') for target in ('web', 'cli')
] + [
    dict(id='desktop-' + platform, app='clients', target='desktop', browser='',
         platform=platform, arch=arch, runner=runner, timeout=180,
         secret='BITWARDEN_CUSTOMIZE_SCRIPT')
    for platform, arch, runner in (('linux', 'x64', 'ubuntu-24.04'),
                                    ('windows', 'x64', 'windows-2022'),
                                    ('macos', 'arm64', 'macos-15'))
] + [dict(id='android', app='android', target='android', browser='', platform='android',
          arch='universal', runner='ubuntu-24.04', timeout=180,
          secret='BITWARDEN_CUSTOMIZE_SCRIPT')]


def select(target):
    choices = {'all', 'clients', 'browser', 'desktop', *(t['id'] for t in TARGETS)}
    if target not in choices:
        raise ValueError('Unknown build target')
    return {'include': [t for t in TARGETS if target in ('all', t['id'], t['target'])
                        or (target == 'clients' and t['app'] == 'clients')]}


if __name__ == '__main__':
    matrix = select(sys.argv[1])
    print('matrix=' + json.dumps(matrix, separators=(',', ':')))
    print('clients=' + str(any(t['app'] == 'clients' for t in matrix['include'])).lower())
