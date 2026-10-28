"""Exercise the installed Android signer and fixed key before compiling the app."""
import os
from pathlib import Path
import subprocess
import tempfile
from android_signing import verify


def main():
    tools = Path(os.environ['ANDROID_HOME'])/'build-tools/37.0.0'
    platform = Path(os.environ['ANDROID_HOME'])/'platforms/android-37.0/android.jar'
    with tempfile.TemporaryDirectory(prefix='signing-check-', dir=os.environ['RUNNER_TEMP']) as directory:
        root = Path(directory)
        manifest = root/'AndroidManifest.xml'
        manifest.write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.example.signingcheck">
<uses-sdk android:minSdkVersion="28" android:targetSdkVersion="37"/><application/></manifest>''')
        unsigned, signed = root/'unsigned.apk', root/'signed.apk'
        subprocess.run([str(tools/'aapt2'),'link','--manifest',str(manifest),'-I',str(platform),'-o',str(unsigned)],check=True)
        subprocess.run([str(tools/'apksigner'),'sign','--ks',os.environ['ANDROID_SIGNING_STORE'],
                        '--ks-key-alias',os.environ['ANDROID_SIGNING_ALIAS'],
                        '--ks-pass','env:ANDROID_SIGNING_PASSWORD','--key-pass','env:ANDROID_SIGNING_PASSWORD',
                        '--v4-signing-enabled','false','--out',str(signed),str(unsigned)],check=True)
        verify(tools/'apksigner',signed,'release-certificate.sha256')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        message = str(error).replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print('::error title=Release signing check::'+message,flush=True)
        raise
