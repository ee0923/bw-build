"""Exercise direct release publication offline with local fixture packages."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('publish-release.py'))
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)
LOCKS = {'clients': {'ref': 'browser-v2026.10.0'}, 'android': {'ref': 'v2026.10.0-bwpm'}}


class ReleaseTests(unittest.TestCase):
    def test_version_comes_from_both_locked_upstreams(self):
        self.assertEqual(release.version(LOCKS), '2026.10.0')
        with self.assertRaises(ValueError):
            release.version({**LOCKS, 'android': {'ref': 'v2026.9.0-bwpm'}})

    def scenario(self, *, tamper=False, extra=False, existing=False, race=False, upload_failure=False):
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            os.chdir(temporary)
            try:
                Path('sources.lock.json').write_text(json.dumps(LOCKS))
                Path('dist').mkdir()
                Path('dist/app.apk').write_bytes(b'package')
                Path('dist/SHA256SUMS').write_text(hashlib.sha256(b'package').hexdigest()+'  app.apk\n')
                if tamper: Path('dist/app.apk').write_bytes(b'changed')
                if extra: Path('dist/private.key').write_text('must not upload')
                calls = []

                def gh(*args, **kwargs):
                    calls.append(args)
                    if race and args[1] == 'create' and sum(c[1]=='create' for c in calls)==1:
                        raise subprocess.CalledProcessError(1, ['gh', *args])
                    if upload_failure and args[1] == 'upload' and sum(c[1]=='upload' for c in calls)==1:
                        raise subprocess.CalledProcessError(1, ['gh', *args])
                    return ''

                with patch.dict(os.environ, GH_REPO='fixture/repo', GITHUB_SHA='a'*40,
                                PACKAGE_ID='bitwarden-android-universal'), \
                        patch.object(release, 'gh', side_effect=gh), \
                        patch.object(release.subprocess, 'run') as view, \
                        patch.object(release.time, 'sleep') as sleep:
                    view.return_value.returncode = 0 if existing else 1
                    if tamper or extra:
                        with self.assertRaises(ValueError): release.publish()
                        view.assert_not_called()
                        self.assertEqual(calls, [])
                    else:
                        release.publish()
                        self.assertEqual(set(p.name for p in Path('release-assets').iterdir()),
                                         {'app.apk', 'SHA256SUMS-bitwarden-android-universal'})
                        self.assertTrue(all(c[0]=='release' for c in calls))
                        self.assertTrue(all(c[2]=='v2026.10.0' for c in calls))
                        self.assertEqual(calls[-1][1], 'edit')
                        self.assertIn('--draft=false', calls[-1])
                        self.assertEqual(calls[-1][calls[-1].index('--notes')+1], 'Custom build.')
                        self.assertFalse(any('Debug APK' in value for call in calls for value in call))
                        if existing: self.assertFalse(any(c[1]=='create' for c in calls))
                        if race or upload_failure: sleep.assert_called_once_with(5)
            finally:
                os.chdir(previous)

    def test_publish_each_verified_target_without_downloading_artifacts(self):
        self.scenario()
        self.scenario(existing=True)

    def test_retry_release_creation_races_and_transient_upload_failures(self):
        self.scenario(race=True)
        self.scenario(upload_failure=True)

    def test_reject_tampering_and_extra_files_before_any_network_call(self):
        self.scenario(tamper=True)
        self.scenario(extra=True)

    def test_reject_manifest_escape_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            (folder/'SHA256SUMS').write_text('a'*64+'  ../private.key\n')
            with self.assertRaises(ValueError): release.verify_packages(folder)
            (folder/'app.apk').symlink_to(folder/'SHA256SUMS')
            (folder/'SHA256SUMS').write_text('a'*64+'  app.apk\n')
            with self.assertRaises(ValueError): release.verify_packages(folder)


if __name__ == '__main__':
    unittest.main()
