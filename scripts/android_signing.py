"""Validate verified APK signers against an independently pinned certificate."""
from pathlib import Path
import base64
import hashlib
import re
import subprocess


def certificate_fingerprints(output):
    # Hash the actual certificates instead of parsing apksigner's human-readable labels.
    blocks = re.findall(r'-----BEGIN CERTIFICATE-----(.*?)-----END CERTIFICATE-----', output, re.S)
    return {hashlib.sha256(base64.b64decode(''.join(block.split()), validate=True)).hexdigest()
            for block in blocks}


def verify(apksigner, apk, pin_file):
    pin = Path(pin_file).read_text().strip().lower()
    if not re.fullmatch('[0-9a-f]{64}', pin):
        raise ValueError('Invalid signing certificate pin')
    result = subprocess.run([str(apksigner), 'verify', '--verbose', '--print-certs-pem', str(apk)],
                            check=True, capture_output=True, text=True)
    found = certificate_fingerprints(result.stdout)
    if found != {pin}:
        # Only public certificate/verification details; never signing passwords or key material.
        print(result.stdout)
        print(result.stderr)
        details = (result.stdout + '\n' + result.stderr).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print('::error title=APK certificate output::' + details)
        raise ValueError(f'Release certificate mismatch: expected {pin}, found {sorted(found)}')
    print('Release signature and fixed certificate verified: ' + pin)
