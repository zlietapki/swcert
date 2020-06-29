import os
import re

from . import utils
from .settings import CA_CRT, CA_ETC_PATH, CA_HOME, CA_KEY, CA_OS_PATH


class Ca:
    @staticmethod
    def get_crt_serial(crt):
        """returns Serial Number or False"""
        try:
            complete = utils.subproc_out(run=['openssl', 'x509', '-text', '-noout', '-in', crt],
                                         msg=f'Check CA crt {crt}')
        except RuntimeError:
            return False
        out_decoded = complete.stdout.decode('utf-8')
        m = re.search(r'Serial Number:\n\s*([^\n]+)', out_decoded)
        return m.group(1)

    def __init__(self, ca_key=CA_KEY, ca_crt=CA_CRT):
        self.ca_key = ca_key
        self.ca_crt = ca_crt
        os.makedirs(CA_HOME, exist_ok=True)
        utils.set_real_owner(CA_HOME)

    def find_or_new_ca_key(self):
        if not self.check_ca_key():
            self.make_ca_key()
            ca_key = self.ca_key
            utils.set_real_owner(ca_key)

    def check_ca_key(self):
        ca_key = self.ca_key
        return utils.subproc(run=['openssl', 'rsa', '-check', '-in', ca_key], msg=f'Check CA key {ca_key}')

    def make_ca_key(self):
        ca_key = self.ca_key
        utils.subproc(run=['openssl', 'genrsa', '-out', ca_key], exit_on_fail=True, msg=f'Make CA key {ca_key}')

    def find_or_new_ca_crt(self):
        ca_crt = self.ca_crt
        crt_serial = Ca.get_crt_serial(ca_crt)
        if not crt_serial:
            self.make_ca_crt()
            utils.set_real_owner(ca_crt)
            crt_serial = Ca.get_crt_serial(ca_crt)

        # check CA installed OS
        os_crt_serial = Ca.get_crt_serial(CA_OS_PATH)
        if not os_crt_serial or os_crt_serial != crt_serial:
            utils.copy(ca_crt, CA_OS_PATH)

        # check CA installed to /etc
        etc_crt_serial = Ca.get_crt_serial(CA_ETC_PATH)
        if not etc_crt_serial or etc_crt_serial != crt_serial:
            utils.etc_install()

    def make_ca_crt(self):
        ca_key = self.ca_key
        ca_crt = self.ca_crt
        utils.subproc(run=[
            'openssl', 'req', '-x509', '-new', '-nodes', '-sha256',
            '-days', '10000',
            '-subj', '/CN=First Galactic Empire/O=Death Star/OU=New Order IT Dept',
            '-key', ca_key,
            '-out', ca_crt
        ], msg=f'Make CA crt {ca_crt}', exit_on_fail=True)
