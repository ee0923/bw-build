#!/usr/bin/env bash
set -euo pipefail
root="$(pwd -P)"
: "${ANDROID_HOME:?Android SDK required}"
python3 scripts/default-server.py
source scripts/gradle-tasks.sh
case "${1:?Build phase required}" in
  tests) tasks=("${network_tests[@]}" "${app_tests[@]}") ;;
  build) tasks=(:app:assembleFdroidRelease) ;;
  package) tasks=() ;;
  *) echo 'Unsupported Android build phase' >&2; exit 2 ;;
esac
if (( ${#tasks[@]} )); then
  : "${GITHUB_TOKEN:?Android SDK download requires a GitHub Packages read token}"
  cd source
  bash ./gradlew --init-script "$root/scripts/pinned-android.init.gradle" \
    --no-daemon --no-scan --no-configuration-cache --console=plain \
    --max-workers=2 -Dorg.gradle.jvmargs=-Xmx4g -Pkotlin.compiler.execution.strategy=in-process \
    "${tasks[@]}"
  exit
fi
unset GITHUB_TOKEN
cd "$root"
python3 - <<'PY'
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile
from scripts.android_signing import verify

def report_failure(kind, error, traceback):
    # Publish a useful annotation even when full log access is unavailable.
    message = str(error).split('; strings=',1)[0]
    for key in ('BW_DEFAULT_SERVER_URL','ANDROID_SIGNING_PASSWORD','GITHUB_TOKEN'):
        if os.environ.get(key):
            message = message.replace(os.environ[key], '[redacted]')
    message = message.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
    print('::error title=Android packaging::'+message,flush=True)
    sys.__excepthook__(kind,error,traceback)

sys.excepthook = report_failure

apks = sorted(Path('source/app/build/outputs/apk/fdroid/release').glob('*.apk'))
if len(apks) != 1:
    raise ValueError('Expected one F-Droid release APK')
tools = Path(os.environ['ANDROID_HOME']) / 'build-tools/37.0.0'
Path('dist').mkdir(exist_ok=True)
for apk in apks:
    aligned = Path(os.environ['RUNNER_TEMP']) / 'bitwarden-release-aligned.apk'
    signed = Path('dist/bitwarden-2026.10.0-fdroid-release.apk')
    subprocess.run([str(tools / 'zipalign'), '-P', '16', '-f', '4', str(apk), str(aligned)], check=True)
    try:
        subprocess.run([str(tools/'apksigner'), 'sign', '--ks', os.environ['ANDROID_SIGNING_STORE'],
                        '--ks-key-alias', os.environ['ANDROID_SIGNING_ALIAS'],
                        '--ks-pass', 'env:ANDROID_SIGNING_PASSWORD', '--key-pass', 'env:ANDROID_SIGNING_PASSWORD',
                        '--v4-signing-enabled', 'false',
                        '--out', str(signed), str(aligned)], check=True)
    finally:
        aligned.unlink(missing_ok=True)
    verify(tools/'apksigner', signed, 'release-certificate.sha256')
    apk = signed
    badging = subprocess.check_output([str(tools / 'aapt2'), 'dump', 'badging', str(apk)], text=True)
    if not re.search(r"^package: name='com\.x8bit\.bitwarden'.*versionName='2026\.10\.0-private'", badging, re.M):
        raise ValueError('Unexpected APK package or version')
    if re.search(r'^application-debuggable', badging, re.M):
        raise ValueError('Release APK must not be debuggable')
    with zipfile.ZipFile(apk) as archive:
        if archive.testzip() is not None or not {'AndroidManifest.xml', 'classes.dex'} <= set(archive.namelist()):
            raise ValueError('Invalid APK archive')
        if not any(os.environ['BW_DEFAULT_SERVER_URL'].encode() in archive.read(name)
                   for name in archive.namelist() if re.fullmatch(r'classes[0-9]*\.dex', name)):
            raise ValueError('APK is missing the configured private default server')
PY
python3 - <<'PY'
import os
import runpy
import sys
try:
    sys.argv = ['scripts/audit-artifacts.py','--apk-dir','dist','--profile','bitwarden-android']
    runpy.run_path(sys.argv[0],run_name='__main__')
except Exception as error:
    message = str(error).split('; strings=',1)[0]
    for key in ('BW_DEFAULT_SERVER_URL','ANDROID_SIGNING_PASSWORD'):
        if os.environ.get(key):
            message = message.replace(os.environ[key], '[redacted]')
    message = message.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
    print('::error title=Android artifact audit::'+message,flush=True)
    raise
PY
python3 scripts/checksums.py
