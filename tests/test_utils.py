import os
import os.path
import pwd

import pytest

from swcertificate import utils


class TestSubproc():
    def test_ok(self):
        assert utils.subproc(run=['which', 'bash'], msg='Test message')

    def test_err_no_exit(self):
        assert not utils.subproc(run=['which', 'some123_bin'], msg='Test message')

    def test_err_with_exit(self):
        with pytest.raises(SystemExit) as excinfo:
            assert utils.subproc(run=['some123_bin'], msg='Test message', exit_on_fail=True)
        assert 'No such file or directory' in excinfo.value.code


@pytest.mark.skipif(os.getlogin() == pwd.getpwuid(os.getuid())[0], reason='Not root - skip test')
class TestSetRealOwner():
    def test_ok(self, tmpdir):
        real_user = os.getlogin()

        path = os.path.join(tmpdir, 'some')
        open(path).close()
        real_user = utils.set_real_owner(path)
        file_owner = pwd.getpwuid(os.stat(path).st_uid).pw_name
        assert file_owner != real_user


class TestCopy():
    def test_dst_dir_exists(self, tmpdir):
        src = os.path.join(tmpdir, 'file')
        open(src, 'a').close()
        dst = os.path.join(tmpdir, 'file2')

        assert utils.copy(src, dst) is None
        assert os.path.isfile(dst)

    def test_no_src(self, tmpdir):
        src = os.path.join(tmpdir, 'file')
        dst = os.path.join(tmpdir, 'file2')
        with pytest.raises(FileNotFoundError) as excinfo:
            utils.copy(src, dst)
        assert 'No such file or directory' in excinfo.value.strerror

    def test_subfolder(self, tmpdir):
        src = os.path.join(tmpdir, 'file')
        open(src, 'a').close()
        dst = os.path.join(tmpdir, 'sub', 'folder', 'file2')
        utils.copy(src, dst)
        assert os.path.isfile(dst)

class TestIsInstalled():
    def test_ok(self):
        assert utils.is_installed('echo')

    def test_fail(self):
        assert not utils.is_installed('non existing command')
