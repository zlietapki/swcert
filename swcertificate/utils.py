import os
import os.path
import shutil
import subprocess
import sys


def subproc(run, msg=None, exit_on_fail=False):
    '''return True False'''
    if msg:
        print(msg)
    try:
        subprocess.run(run, check=True, capture_output=True)
    except Exception as e:  # pylint: disable=broad-except
        if hasattr(e, 'stderr'):
            err_msg = getattr(e, 'stderr').decode('utf-8')
        else:
            err_msg = str(e)

        if exit_on_fail:
            sys.exit(err_msg)
        return False
    return True

def subproc_out(run, msg=None):
    '''returns subproc.complete obj'''
    if msg:
        print(msg)

    try:
        complete = subprocess.run(run, check=True, capture_output=True)
    except Exception as e:  # pylint: disable=broad-except
        if hasattr(e, 'stderr'):
            err_msg = getattr(e, 'stderr').decode('utf-8')
        else:
            err_msg = str(e)
        raise RuntimeError(err_msg)
    return complete

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
        raise RuntimeError(e.strerror + '. Run with `sudo`')
        # sys.exit(e.strerror + '. Run with `sudo`')

def etc_install():
    subproc(msg='Update /etc/ssl/certs/', run=['update-ca-certificates', '--fresh'], exit_on_fail=True)

def is_installed(binary_name):
    return subproc(msg=f'Check installed {binary_name}', run=['which', binary_name])
