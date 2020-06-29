import os
import os.path
import re

import pytest

from swcertificate.ca import Ca


class TestCheckCrt:
    def test_ok(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')
        ca_crt = os.path.join(tmpdir, 'some.crt')

        ca = Ca(ca_key=ca_key, ca_crt=ca_crt)
        ca.make_ca_key()
        ca.make_ca_crt()

        serial = Ca.get_crt_serial(ca_crt)
        assert len(serial) == 59
        assert re.search(r'^[a-f0-9:]+$', serial)

    def test_not_exists(self, tmpdir):
        crt = os.path.join(tmpdir, 'some.crt')
        assert not Ca.get_crt_serial(crt)


class TestCheckCaKey:
    def test_not_exists(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')

        ca = Ca(ca_key=ca_key)
        assert not ca.check_ca_key()

    def test_empty(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')
        open(ca_key, 'a').close()

        ca = Ca(ca_key=ca_key)
        assert not ca.check_ca_key()

    def test_ok(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')
        ca = Ca(ca_key=ca_key)
        ca.make_ca_key()
        assert ca.check_ca_key()


class TestMakeCaKey:
    def test_ok(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')
        ca = Ca(ca_key=ca_key)
        assert ca.make_ca_key() is None

    def test_dir_not_exists(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'non_exists', 'some.key')
        ca = Ca(ca_key=ca_key)
        with pytest.raises(SystemExit) as excinfo:
            ca.make_ca_key()
        assert 'No such file or directory' in excinfo.value.code

    def test_write_err(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')
        open(ca_key, 'a').close()
        os.chmod(ca_key, 0o000)

        ca = Ca(ca_key=ca_key)
        with pytest.raises(SystemExit) as excinfo:
            ca.make_ca_key()
        assert 'Permission denied' in excinfo.value.code


class TestMakeCaCrt:
    def test_ok(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')
        ca_crt = os.path.join(tmpdir, 'some.crt')
        ca = Ca(ca_key=ca_key, ca_crt=ca_crt)
        ca.make_ca_key()

        assert ca.make_ca_crt() is None

    def test_no_key(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')
        ca_crt = os.path.join(tmpdir, 'some.crt')
        ca = Ca(ca_key=ca_key, ca_crt=ca_crt)
        with pytest.raises(SystemExit) as excinfo:
            ca.make_ca_crt()
        err_str = excinfo.value.code
        assert 'No such file or directory' in err_str

    def test_write_err(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'some.key')

        ca_crt = os.path.join(tmpdir, 'some.crt')
        open(ca_crt, 'a').close()
        os.chmod(ca_crt, 0o000)

        ca = Ca(ca_key=ca_key, ca_crt=ca_crt)
        ca.make_ca_key()
        with pytest.raises(SystemExit) as excinfo:
            ca.make_ca_crt()
        assert 'Permission denied' in excinfo.value.code
