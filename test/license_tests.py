import unittest
from pprint import pprint

from lichecker import LicenseChecker

# these packages dont define license in setup.py
# manually verified and injected
license_overrides = {
    "kthread": "MIT",
    'yt-dlp': "Unlicense",
    'pyxdg': 'GPL-2.0',
    'ptyprocess': 'ISC',
    'psutil': 'BSD3',
    'setuptools': "MIT"
}
# explicitly allow these packages that would fail otherwise
whitelist = [
    'typing-extensions',  # PSFL
    'idna',  # BSD-like
    'python-dateutil',  # 'Simplified BSD'
    'cryptography',  # 'BSD or Apache License, Version 2.0',
    'pycryptodomex',  # 'BSD, Public Domain',
]

# validation flags
allow_nonfree = False
allow_viral = False
allow_unknown = False
allow_unlicense = True
allow_ambiguous = False

pkg_name = "jarbas_hive_mind"


class TestLicensing(unittest.TestCase):
    licheck = LicenseChecker(pkg_name,
                             license_overrides=license_overrides,
                             whitelisted_packages=whitelist,
                             allow_ambiguous=allow_ambiguous,
                             allow_unlicense=allow_unlicense,
                             allow_unknown=allow_unknown,
                             allow_viral=allow_viral,
                             allow_nonfree=allow_nonfree)

    def test_license_compliance(self):
        print("Package", pkg_name)
        print("Version", self.licheck.version)
        print("License", self.licheck.license)
        print("Transient Requirements (dependencies of dependencies)")
        pprint(self.licheck.transient_dependencies)

        print("Package Versions")
        pprint(self.licheck.versions)

        print("Dependency Licenses")
        pprint(self.licheck.licenses)

        self.licheck.validate()
