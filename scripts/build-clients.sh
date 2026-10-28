#!/usr/bin/env bash
set -euo pipefail
root="$(pwd -P)"
export HUSKY=0 ELECTRON_SKIP_BINARY_DOWNLOAD=1
python3 scripts/default-server.py
cd source
case "${1:?Build phase required}" in
  dependencies) npm ci --ignore-scripts --no-audit --no-fund; exit ;;
  native)
    (cd apps/desktop/desktop_native && rustup show active-toolchain && node build.js --release)
    exit ;;
  build) ;;
  package)
    cd "$root"
    python3 scripts/package-clients.py
    if [[ "$BW_BUILD_TARGET" == desktop ]]; then
      unset ELECTRON_SKIP_BINARY_DOWNLOAD
      (cd source/apps/desktop && node ../../node_modules/electron-builder/out/cli/cli.js \
        --config "$root/scripts/desktop-config.cjs" --publish never)
      python3 scripts/package-clients.py --desktop-output
    fi
    python3 scripts/checksums.py
    exit ;;
  *) echo 'Unsupported build phase' >&2; exit 2 ;;
esac
case "${BW_BUILD_TARGET:?Build target required}" in
  browser)
    case "${BW_BUILD_BROWSER:?Browser required}" in chrome|edge|firefox) ;; *) exit 2 ;; esac
    npm run "build:prod:$BW_BUILD_BROWSER" --workspace @bitwarden/browser ;;
  web) npm run build:oss:selfhost:prod --workspace @bitwarden/web-vault ;;
  cli)
    npm run build:oss:prod --workspace @bitwarden/cli
    node apps/cli/build/bw.js --version ;;
  desktop)
    npm run build:oss --workspace @bitwarden/desktop ;;
  *) echo 'Unsupported client build target' >&2; exit 2 ;;
esac
