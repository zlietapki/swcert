import os
import os.path
import subprocess

from swcertificate import Ca, Nss
from swcertificate.settings import NSS_NAME


class TestNssFind():
    def test_not_found(self, tmpdir):
        folder = os.path.join(tmpdir, 'some/other/folder')
        os.makedirs(folder)

        nss = Nss(nss_dirs=[tmpdir])
        nss_dirs = nss.find()
        assert not nss_dirs

    def test_found(self, tmpdir):
        folder = os.path.join(tmpdir, 'some/other/folder')
        os.makedirs(folder)
        nss_db_path = os.path.join(folder, NSS_NAME)
        open(nss_db_path, 'a').close()

        nss = Nss(nss_dirs=[tmpdir])
        nss_dirs = nss.find()
        assert folder in nss_dirs


class TestNssInstall():
    def test_nss_install_cert(self, tmpdir):
        # create CA
        ca_key = os.path.join(tmpdir, 'some.key')
        ca_crt = os.path.join(tmpdir, 'some.crt')
        ca = Ca(ca_key=ca_key, ca_crt=ca_crt)
        ca.make_ca_key()
        ca.make_ca_crt()

        # create NSS databases
        nss_dirs = (os.path.join(tmpdir, 'my_nss'), os.path.join(tmpdir, 'my_nss2'))
        for nss_dir in nss_dirs:
            os.makedirs(nss_dir)
            subprocess.run(['certutil', '-N', '-d', nss_dir, '--empty-password'], check=True)

        nss = Nss()
        for nss_dir in nss_dirs:
            nss.install_cert(nss_dir=nss_dir, crt=ca_crt)
            assert nss.check_cert(nss_dir=nss_dir)


class TestCheckNss():
    def test_nss_check_for_cert(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')
        ca_crt = os.path.join(tmpdir, 'some.crt')

        ca = Ca(ca_key=ca_key, ca_crt=ca_crt)
        ca.make_ca_key()
        ca.make_ca_crt()

        nss_dir = os.path.join(tmpdir, 'my_nss')
        os.makedirs(nss_dir)
        subprocess.run(['certutil', '-N', '-d', nss_dir, '--empty-password'], check=True)
        nss = Nss()
        nss.install_cert(nss_dir=nss_dir, crt=ca_crt, cert_name='myname')

        assert not nss.check_cert(nss_dir=nss_dir, cert_name='not myname')
        assert nss.check_cert(nss_dir=nss_dir, cert_name='myname')
