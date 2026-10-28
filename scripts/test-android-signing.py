"""Fail closed on wrong/missing certificates and unsuccessful APK verification."""
import base64
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import android_signing


class SigningTests(unittest.TestCase):
    def test_pem_fingerprints_ignore_signer_label_formats(self):
        certificate = b'certificate encoded by apksigner'
        pem = '-----BEGIN CERTIFICATE-----\r\n' + base64.b64encode(certificate).decode() + '\r\n-----END CERTIFICATE-----'
        for label in ('Signer #1', 'Signer (minSdkVersion=28, maxSdkVersion=2147483647)', 'Future signer label'):
            with self.subTest(label=label):
                self.assertEqual(android_signing.certificate_fingerprints(label+'\n'+pem),
                                 {hashlib.sha256(certificate).hexdigest()})
        self.assertEqual(android_signing.certificate_fingerprints('Signer #1 public key SHA-256 digest: '+'ab'*32), set())
        with self.assertRaises(ValueError):
            android_signing.certificate_fingerprints('-----BEGIN CERTIFICATE-----!-----END CERTIFICATE-----')

    def test_verification_requires_success_and_the_exact_pinned_certificate(self):
        cert = b'expected certificate'
        pem = '-----BEGIN CERTIFICATE-----\n'+base64.b64encode(cert).decode()+'\n-----END CERTIFICATE-----'
        other = '-----BEGIN CERTIFICATE-----\n'+base64.b64encode(b'other certificate').decode()+'\n-----END CERTIFICATE-----'
        with tempfile.TemporaryDirectory() as directory:
            pin = Path(directory)/'pin'
            pin.write_text(hashlib.sha256(cert).hexdigest()+'\n')
            for output, accepted in ((pem,True),(pem+pem,True),(pem+other,False),(other,False),('',False)):
                with self.subTest(output=output), patch.object(android_signing.subprocess, 'run',
                        return_value=subprocess.CompletedProcess([],0,output,'')) as run, patch('builtins.print'):
                    if accepted:
                        android_signing.verify('apksigner','app.apk',pin)
                    else:
                        with self.assertRaisesRegex(ValueError, 'certificate mismatch'):
                            android_signing.verify('apksigner','app.apk',pin)
                    self.assertIn('--print-certs-pem',run.call_args.args[0])
            with patch.object(android_signing.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['apksigner'])):
                with self.assertRaises(subprocess.CalledProcessError):
                    android_signing.verify('apksigner','app.apk',pin)


if __name__ == '__main__':
    unittest.main()
