import os
import os.path
import shutil
import subprocess
import sys


def subproc(msg, run, ok_msg='OK', fail_msg='error', exit_on_fail=False):
    print(f'{msg} - ', end='')
    try:
        subprocess.run(run, check=True, capture_output=True)
    except Exception as e:  # pylint: disable=broad-except
        print(fail_msg)
        if hasattr(e, 'stderr'):
            err_msg = getattr(e, 'stderr').decode('utf-8')
        else:
            err_msg = str(e)

        if exit_on_fail:
            sys.exit(err_msg)
        return False
    print(ok_msg)
    return True

def set_real_owner(path):
    owner = os.getlogin()
    shutil.chown(path, user=owner, group=owner)

def copy(src, dst):
    print(f'Copy {src} -> {dst}')
    dst_dir = os.path.dirname(dst)
    try:
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        shutil.copyfile(src, dst)
    except PermissionError as e:
        print('Error')
        sys.exit(e.strerror + '. Run with `sudo`')

def etc_install():
    subproc(msg='Update /etc/ssl/certs/', run=['update-ca-certificates', '--fresh'], exit_on_fail=True)

def is_installed(binary_name):
    return subproc(msg=f'Check installed {binary_name}', run=['which', binary_name])
