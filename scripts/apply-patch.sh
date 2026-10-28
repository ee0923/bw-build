#!/usr/bin/env bash
set -euo pipefail
set +x
: "${PATCH_BOOTSTRAP:?Configure the BITWARDEN_CUSTOMIZE_SCRIPT repository secret first}"
: "${RUNNER_TEMP:?Run inside GitHub Actions}"
export SOURCE
SOURCE="$(python3 -c 'from pathlib import Path; print(Path("source").resolve())')"
export BITWARDEN_BUILD_BASH
BITWARDEN_BUILD_BASH="$BASH"
if command -v cygpath >/dev/null; then
  BITWARDEN_BUILD_BASH="$(cygpath -w "$BASH")"
fi
bootstrap="$(mktemp "$RUNNER_TEMP/bitwarden-bootstrap.XXXXXX")"
trap 'rm -f "$bootstrap"' EXIT
chmod 600 "$bootstrap"
printf '%s\n' "$PATCH_BOOTSTRAP" > "$bootstrap"
unset PATCH_BOOTSTRAP
# The fixed bootstrap downloads once, authenticates and decrypts before execution.
bash "$bootstrap" "$@"
