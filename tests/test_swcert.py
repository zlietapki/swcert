import getpass
import os
import os.path
import pwd
import subprocess

import pytest

from swcert import (NSS_NAME, add_domain, check_ca_key, check_crt, copy,
                    delete_domain, make_ca_crt, make_ca_key, nss_check_cert,
                    nss_find, nss_install_cert, set_real_owner, subproc)


class TestSubproc():
    def test_ok(self):
        assert subproc(msg='Test message', run=['which', 'bash'])

    def test_err_no_exit(self):
        assert not subproc(msg='Test message', run=['which', 'some123_bin'])

    def test_err_with_exit(self):
        with pytest.raises(SystemExit) as excinfo:
            assert subproc(msg='Test message', run=['some123_bin'], exit_on_fail=True)
        assert 'No such file or directory' in excinfo.value.code


@pytest.mark.skipif(os.getlogin() == pwd.getpwuid(os.getuid())[0], reason='Not root - skip test')
class TestSetRealOwner():
    def test_ok(self, tmpdir):
        real_user = os.getlogin()

        path = os.path.join(tmpdir, 'some')
        open(path).close()
        real_user = set_real_owner(path)
        file_owner = pwd.getpwuid(os.stat(path).st_uid).pw_name
        assert file_owner != real_user


class TestCheckKey():
    def test_not_exists(self, tmpdir):
        key = os.path.join(tmpdir, 'some.key')
        assert not check_ca_key(key)


class TestCheckCrt():
    def test_not_exists(self, tmpdir):
        crt = os.path.join(tmpdir, 'some.crt')
        assert not check_crt(crt)


class TestMakeCAKey():
    def test_dir_not_exists(self, tmpdir):
        key = os.path.join(tmpdir, 'non_exists', 'some.key')
        with pytest.raises(SystemExit) as excinfo:
            make_ca_key(key)
        assert 'No such file or directory' in excinfo.value.code

    def test_write_err(self, tmpdir):
        key = os.path.join(tmpdir, 'some.key')
        open(key, 'a').close()
        os.chmod(key, 0o000)

        with pytest.raises(SystemExit) as excinfo:
            make_ca_key(key)
        assert 'Permission denied' in excinfo.value.code

    def test_ok(self, tmpdir):
        key = os.path.join(tmpdir, 'some.key')
        assert make_ca_key(key)


class TestMakeCaCrt():
    def test_no_key(self, tmpdir):
        key = os.path.join(tmpdir, 'some.key')
        crt = os.path.join(tmpdir, 'some.crt')
        with pytest.raises(SystemExit) as excinfo:
            make_ca_crt(crt=crt, key=key)
        err_str = excinfo.value.code
        assert 'No such file or directory' in err_str

    def test_write_err(self, tmpdir):
        key = os.path.join(tmpdir, 'some.key')
        make_ca_key(key)

        crt = os.path.join(tmpdir, 'some.crt')
        open(crt, 'a').close()
        os.chmod(crt, 0o000)

        with pytest.raises(SystemExit) as excinfo:
            make_ca_crt(crt=crt, key=key)
        assert 'Permission denied' in excinfo.value.code

    def test_ok(self, tmpdir):
        key = os.path.join(tmpdir, 'some.key')
        make_ca_key(key)

        crt = os.path.join(tmpdir, 'some.crt')
        assert make_ca_crt(crt=crt, key=key)


class TestCopy():
    def test_dst_dir_exists(self, tmpdir):
        src = os.path.join(tmpdir, 'file')
        open(src, 'a').close()
        dst = os.path.join(tmpdir, 'file2')

        assert copy(src, dst)
        assert os.path.isfile(dst)

    def test_no_src(self, tmpdir):
        src = os.path.join(tmpdir, 'file')
        dst = os.path.join(tmpdir, 'file2')
        with pytest.raises(FileNotFoundError) as excinfo:
            copy(src, dst)
        assert 'No such file or directory' in excinfo.value.strerror

    def test_subfolder(self, tmpdir):
        src = os.path.join(tmpdir, 'file')
        open(src, 'a').close()
        dst = os.path.join(tmpdir, 'sub', 'folder', 'file2')
        copy(src, dst)
        assert os.path.isfile(dst)


class TestNssFind():
    def test_not_found(self, tmpdir):
        folder = os.path.join(tmpdir, 'some/other/folder')
        os.makedirs(folder)

        nss = nss_find(NSS_NAME, [tmpdir])
        assert not len(nss)

    def test_found(self, tmpdir):
        folder = os.path.join(tmpdir, 'some/other/folder')
        os.makedirs(folder)
        nss_db_path = os.path.join(folder, NSS_NAME)
        open(nss_db_path, 'a').close()

        nss = nss_find(NSS_NAME, [tmpdir])
        assert folder in nss


class TestNssInstall():
    def test_nss_install_cert(self, tmpdir):
        # create CA
        key = os.path.join(tmpdir, 'some.key')
        make_ca_key(key)
        crt = os.path.join(tmpdir, 'some.crt')
        make_ca_crt(crt=crt, key=key)

        # create NSS databases
        nss_dirs = (os.path.join(tmpdir, 'my_nss'), os.path.join(tmpdir, 'my_nss2'))
        for nss in nss_dirs:
            os.makedirs(nss)
            subprocess.run(['certutil', '-N', '-d', nss, '--empty-password'], check=True)

        for nss in nss_dirs:
            nss_install_cert(nss=nss, crt=crt)
            assert nss_check_cert(nss=nss)


class TestCheckNss():
    def test_nss_check_for_cert(self, tmpdir):
        key = os.path.join(tmpdir, 'some.key')
        make_ca_key(key)
        crt = os.path.join(tmpdir, 'some.crt')
        make_ca_crt(crt=crt, key=key)

        nss = os.path.join(tmpdir, 'my_nss')
        os.makedirs(nss)
        subprocess.run(['certutil', '-N', '-d', nss, '--empty-password'], check=True)
        nss_install_cert(nss=nss, crt=crt, cert_name='myname')

        assert not nss_check_cert(nss=nss, cert_name='not myname')
        assert nss_check_cert(nss=nss, cert_name='myname')


class TestDomain():
    def test_add_domain(self, tmpdir):
        domain = os.path.join(tmpdir, 'domain.lan')
        add_domain(cert_list=tmpdir, domain=domain)
        assert os.path.isfile(domain)

    def test_delete_domain(self, tmpdir):
        domain = os.path.join(tmpdir, 'domain.lan')
        open(domain, 'a').close()
        delete_domain(cert_list=tmpdir, domain=domain)
        assert not os.path.isfile(domain)
