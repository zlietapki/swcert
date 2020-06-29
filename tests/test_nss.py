import os
import os.path
import re
import subprocess

from swcertificate import Ca, Nss
from swcertificate.settings import NSS_NAME


class TestNssFind:
    def test_not_found(self, tmpdir):
        folder = os.path.join(tmpdir, 'some/other/folder')
        os.makedirs(folder)

        nss_dirs = Nss.find(nss_dirs=[tmpdir])
        assert not nss_dirs

    def test_found(self, tmpdir):
        folder = os.path.join(tmpdir, 'some/other/folder')
        os.makedirs(folder)
        nss_db_path = os.path.join(folder, NSS_NAME)
        open(nss_db_path, 'a').close()

        nss_dirs = Nss.find(nss_dirs=[tmpdir])
        assert folder in nss_dirs


class TestGetSerial:
    def test_ok(self, tmpdir):
        # create CA
        ca_key = os.path.join(tmpdir, 'some.key')
        ca_crt = os.path.join(tmpdir, 'some.crt')
        ca = Ca(ca_key=ca_key, ca_crt=ca_crt)
        ca.make_ca_key()
        ca.make_ca_crt()

        # create NSS databases
        nss_dir = os.path.join(tmpdir, 'my_nss')
        os.makedirs(nss_dir)
        subprocess.run(['certutil', '-N', '-d', nss_dir, '--empty-password'], check=True)

        # install CA to NSS
        Nss.install_ca(nss_dir, ca_crt, cert_name='test cert')
        # Check NSS CA
        serial = Nss.get_crt_serial(nss_dir, cert_name='test cert')
        assert len(serial) == 59
        assert re.search(r'^[a-f0-9:]+$', serial)


class TestDeleteCert:
    def test_ok(self, tmpdir):
        # create CA
        ca_key = os.path.join(tmpdir, 'some.key')
        ca_crt = os.path.join(tmpdir, 'some.crt')
        ca = Ca(ca_key=ca_key, ca_crt=ca_crt)
        ca.make_ca_key()
        ca.make_ca_crt()

        # create NSS databases
        nss_dir = os.path.join(tmpdir, 'my_nss')
        os.makedirs(nss_dir)
        subprocess.run(['certutil', '-N', '-d', nss_dir, '--empty-password'], check=True)

        # install CA to NSS
        Nss.install_ca(nss_dir, ca_crt, cert_name='test cert')
        assert Nss.get_crt_serial(nss_dir, cert_name='test cert')

        # delete CA from nss
        Nss.delete_cert(nss_dir, cert_name='test cert')
        # check
        assert not Nss.get_crt_serial(nss_dir, cert_name='test cert')

    def test_del_multi(self, tmpdir):
        # create NSS databases
        nss_dir = os.path.join(tmpdir, 'my_nss')
        os.makedirs(nss_dir)
        subprocess.run(['certutil', '-N', '-d', nss_dir, '--empty-password'], check=True)

        ca_key = os.path.join(tmpdir, 'some1.key')

        # create CA
        ca_crt1 = os.path.join(tmpdir, 'some1.crt')
        ca1 = Ca(ca_key=ca_key, ca_crt=ca_crt1)
        ca1.make_ca_key()
        ca1.make_ca_crt()

        # install CA to NSS
        Nss.install_ca(nss_dir, ca_crt1, cert_name='test cert')

        # create CA
        ca_crt2 = os.path.join(tmpdir, 'some2.crt')
        ca2 = Ca(ca_key=ca_key, ca_crt=ca_crt2)
        ca2.make_ca_key()
        ca2.make_ca_crt()

        # install CA to NSS
        Nss.install_ca(nss_dir, ca_crt2, cert_name='test cert')

        # delete all certs by name
        Nss.delete_cert(nss_dir, cert_name='test cert')

        assert not Nss.get_crt_serial(nss_dir, cert_name='test cert')


class TestInstallCa:
    def test_ok(self, tmpdir):
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

        # install CA to NSS
        for nss_dir in nss_dirs:
            Nss.install_ca(nss_dir, ca_crt, cert_name='test cert')
            # Check NSS CA
            assert Nss.get_crt_serial(nss_dir, cert_name='test cert')
