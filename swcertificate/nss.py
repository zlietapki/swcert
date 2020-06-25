import os
import re

from . import utils
from .settings import CA_CRT, NSS_CERT_NAME, NSS_DIRS, NSS_NAME


class Nss():
    @staticmethod
    def find(nss_name=NSS_NAME, nss_dirs=NSS_DIRS):
        found_nss_dirs = []
        for nss_dir in nss_dirs:
            for root, _dirs, files in os.walk(nss_dir):
                if nss_name in files:
                    found_nss_dirs.append(root)
        return found_nss_dirs


    @staticmethod
    def get_crt_serial(nss_dir, cert_name=NSS_CERT_NAME):
        '''return Serial Number or False'''
        print(f'Get NSS cert serial `{cert_name}` {nss_dir}')
        try:
            complete = utils.subproc_out(run=['certutil', '-L', '-n', cert_name, '-d', nss_dir])
        except RuntimeError:
            return False

        out_decoded = complete.stdout.decode('utf-8')
        m = re.search(r'Serial Number:\n\s*([^\n]+)', out_decoded)
        serial = m.group(1)
        print(f'Serial { serial }')
        return serial

    @staticmethod
    def delete_cert(nss_dir, cert_name=NSS_CERT_NAME):
        print(f'Delete NSS CA {cert_name} from {nss_dir}')
        try:
            while Nss.get_crt_serial(nss_dir, cert_name=cert_name):
                utils.subproc(run=['certutil', '-D', '-n', cert_name, '-d', nss_dir], exit_on_fail=True)
        except RuntimeError:
            pass

    @staticmethod
    def install_ca(nss_dir, ca_crt=CA_CRT, cert_name=NSS_CERT_NAME):
        print(f'Install NSS CA {cert_name} from {ca_crt} to {nss_dir}')
        utils.subproc(run=['certutil', '-A', '-n', cert_name, '-t', 'TC,C,T', '-d', nss_dir, '-i', ca_crt], exit_on_fail=True)
