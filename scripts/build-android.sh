#!/usr/bin/env bash
set -euo pipefail
root="$(pwd -P)"
: "${ANDROID_HOME:?Android SDK required}"
python3 scripts/default-server.py
source scripts/gradle-tasks.sh
case "${1:?Build phase required}" in
  tests) tasks=("${network_tests[@]}" "${app_tests[@]}") ;;
  build) tasks=(:app:assembleFdroidDebug) ;;
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
import zipfile

apks = sorted(Path('source/app/build/outputs/apk/fdroid/debug').glob('*.apk'))
if not apks:
    raise SystemExit('No F-Droid debug APK was produced')
tools = Path(os.environ['ANDROID_HOME']) / 'build-tools/37.0.0'
Path('dist').mkdir(exist_ok=True)
for apk in apks:
    subprocess.run([str(tools / 'apksigner'), 'verify', str(apk)], check=True)
    badging = subprocess.check_output([str(tools / 'aapt2'), 'dump', 'badging', str(apk)], text=True)
    if not re.search(r"^package: name='com\.x8bit\.bitwarden\.dev'.*versionName='2026\.10\.0-private'", badging, re.M):
        raise SystemExit('Unexpected APK package or version')
    with zipfile.ZipFile(apk) as archive:
        if archive.testzip() is not None or not {'AndroidManifest.xml', 'classes.dex'} <= set(archive.namelist()):
            raise SystemExit('Invalid APK archive')
        if not any(os.environ['BW_DEFAULT_SERVER_URL'].encode() in archive.read(name)
                   for name in archive.namelist() if re.fullmatch(r'classes[0-9]*\.dex', name)):
            raise SystemExit('APK is missing the configured private default server')
    shutil.copy2(apk, Path('dist') / apk.name)
PY
python3 scripts/checksums.py
