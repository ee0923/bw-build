#!/usr/bin/env bash
set -euo pipefail
unset BW_DEFAULT_SERVER_URL
cd source
  node node_modules/jest/bin/jest.js --config libs/logging/jest.config.js --runInBand
  node node_modules/jest/bin/jest.js --config libs/common/jest.config.js --runInBand --runTestsByPath \
    libs/common/src/services/audit.service.spec.ts \
    libs/common/src/dirt/services/hibp-api.service.spec.ts \
    libs/common/src/vault/icon/build-cipher-icon.spec.ts \
    libs/common/src/platform/abstractions/sdk/sdk-load.privacy.spec.ts \
    libs/common/src/platform/services/default-environment.service.spec.ts \
    libs/common/src/platform/services/default-environment.private.spec.ts \
    libs/common/src/platform/misc/server-address.spec.ts \
    libs/common/src/platform/misc/private-server-policy.spec.ts \
    libs/common/src/platform/misc/private-runtime-policy.spec.ts \
    libs/common/src/platform/services/sdk/private-sdk-settings.spec.ts \
    libs/common/src/platform/services/sdk/default-sdk.service.spec.ts \
    libs/common/src/platform/services/sdk/register-sdk.service.spec.ts
  node node_modules/jest/bin/jest.js --config libs/angular/jest.config.js --runInBand --runTestsByPath \
    libs/angular/src/auth/environment-selector/environment-selector.component.spec.ts \
    libs/angular/src/auth/login-via-webauthn/login-via-webauthn.compatibility.spec.ts
  node node_modules/jest/bin/jest.js --config libs/components/jest.config.js --runInBand --runTestsByPath \
    libs/components/src/dialog/dialog.service.spec.ts
  node node_modules/jest/bin/jest.js --config libs/auth/jest.config.js --runInBand --runTestsByPath \
    libs/auth/src/angular/input-password/input-password.privacy.spec.ts
  node node_modules/jest/bin/jest.js --config apps/browser/jest.config.js --runInBand --runTestsByPath \
    apps/browser/src/platform/services/browser-initial-install.service.spec.ts \
    apps/browser/src/autofill/services/targeting-rules-data.service.spec.ts \
    apps/browser/src/platform/browser/browser-api.lifecycle.spec.ts \
    apps/browser/src/autofill/services/inline-menu-field-qualification.service.spec.ts \
    apps/browser/src/autofill/services/autofill-triage.service.spec.ts \
    apps/browser/src/autofill/background/overlay.background.spec.ts \
    apps/browser/src/platform/services/platform-utils/browser-platform-utils.service.spec.ts \
    apps/browser/src/platform/offscreen-document/offscreen-document.service.spec.ts \
    apps/browser/src/platform/offscreen-document/offscreen-document.spec.ts \
    apps/browser/src/platform/messaging/runtime-notification.spec.ts \
    apps/browser/src/autofill/content/content-message-handler.spec.ts \
    apps/browser/src/autofill/services/autofill-lifecycle.service.spec.ts \
    apps/browser/src/platform/services/task-scheduler/background-task-scheduler.service.spec.ts \
    apps/browser/src/autofill/content/trigger-autofill-script-injection.spec.ts \
    apps/browser/src/autofill/services/collect-autofill-content.service.spec.ts \
    apps/browser/src/background/runtime.background.spec.ts \
    apps/browser/src/auth/popup/account-switching/services/account-switcher.service.spec.ts \
    apps/browser/src/platform/browser/browser-api.spec.ts \
    apps/browser/src/platform/services/private-network-rules.spec.ts \
    apps/browser/src/autofill/services/autofill.service.spec.ts \
    apps/browser/src/platform/services/browser-script-injector.service.spec.ts
  node node_modules/jest/bin/jest.js --config apps/desktop/jest.config.js --runInBand --runTestsByPath \
    apps/desktop/src/platform/services/electron-log.service.spec.ts apps/desktop/src/main/updater.privacy.spec.ts \
    apps/desktop/src/platform/main/safe-shell.main.spec.ts
  node node_modules/jest/bin/jest.js --config apps/cli/jest.config.js --runInBand --runTestsByPath \
    apps/cli/src/platform/services/console-log.service.spec.ts apps/cli/src/commands/update.privacy.spec.ts \
    apps/cli/src/tools/send/models/send.response.privacy.spec.ts
  node node_modules/jest/bin/jest.js --config apps/web/jest.config.js --runInBand --runTestsByPath \
    apps/web/src/app/dirt/reports/pages/exposed-passwords-report.component.spec.ts \
    apps/web/src/app/dirt/reports/pages/breach-report.component.spec.ts \
    apps/web/src/app/platform/web-environment.service.spec.ts
