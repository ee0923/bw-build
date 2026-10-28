// Preserve upstream native resources and hardening, with local packaging and no publishing.
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');
const { createRequire } = require('module');
const desktop = path.resolve('source/apps/desktop');
// electron-builder loads this file while its working directory is apps/desktop.
const root = fs.existsSync(path.join(desktop, 'electron-builder.json')) ? desktop : process.cwd();
const sourceRequire = createRequire(path.join(root, 'package.json'));
const { flipFuses } = sourceRequire('@electron/fuses');
const config = require(path.join(root, 'electron-builder.json'));
config.publish = null;
config.generateUpdatesFilesForAllChannels = false;
config.afterSign = null;
config.artifactName = 'bitwarden-desktop-${version}-${os}-${arch}.${ext}';
config.linux.target = [{ target: 'tar.gz', arch: ['x64'] }];
config.win.target = [{ target: 'zip', arch: ['x64'] }];
delete config.win.signtoolOptions;
config.win.signAndEditExecutable = false;
config.mac.target = [{ target: 'dmg', arch: ['arm64'] }, { target: 'zip', arch: ['arm64'] }];
delete config.mac.sign;
delete config.mac.provisioningProfile;
config.mac.identity = '-';
config.mac.notarize = false;
const upstreamAfterPack = require(path.join(root, 'scripts/after-pack.js')).default;
config.afterPack = async (context) => {
  if (context.electronPlatformName !== 'darwin') return upstreamAfterPack(context);
  // This unsigned distribution has no App Store/Safari extension or developer certificate.
  const { electronFuses } = require(path.join(root, 'scripts/electron-fuses.js'));
  const app = path.join(context.appOutDir, context.packager.appInfo.productFilename + '.app');
  await flipFuses(app, { ...electronFuses('darwin'), resetAdHocDarwinSignature: true });
  for (const name of ['desktop_proxy', 'desktop_proxy.inherit']) {
    execFileSync('codesign', ['--force', '--sign', '-', '--options', 'runtime', '--entitlements',
      path.join(root, 'resources/entitlements.mac.inherit.plist'), path.join(app, 'Contents/MacOS', name)]);
  }
};
module.exports = config;
