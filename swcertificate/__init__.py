# empty list
# sudo with alert


import os
import shutil
import subprocess
import sys
from os import listdir
from os.path import basename, dirname, isfile

from . import utils
from .settings import (CA_CRT, CA_ETC_PATH, CA_HOME, CA_KEY, CA_OS_PATH,
                       CA_SRL, CERT_CRT, CERT_CSR, CERT_KEY, CERT_LIST,
                       NSS_CERT_NAME, NSS_DIRS, NSS_NAME, SW_HOME)


class Ca():
    @staticmethod
    def check_crt(crt):
        return utils.subproc(msg=f'Check CA crt {crt}', run=['openssl', 'x509', '-text', '-noout', '-in', crt])

    def __init__(self, ca_key=CA_KEY, ca_crt=CA_CRT):
        self.ca_key = ca_key
        self.ca_crt = ca_crt
        os.makedirs(CA_HOME, exist_ok=True)


    def find_or_new_ca_key(self):
        if not self.check_ca_key():
            self.make_ca_key()
            ca_key = self.ca_key
            utils.set_real_owner(ca_key)

    def check_ca_key(self):
        ca_key = self.ca_key
        return utils.subproc(msg=f'Check CA key {ca_key}', run=['openssl', 'rsa', '-check', '-in', ca_key])

    def make_ca_key(self):
        ca_key = self.ca_key
        utils.subproc(msg=f'Make CA key {ca_key}', run=['openssl', 'genrsa', '-out', ca_key], exit_on_fail=True)

    def find_or_new_ca_crt(self):
        ca_crt = self.ca_crt
        if not Ca.check_crt(ca_crt):
            self.make_ca_crt()
            utils.set_real_owner(ca_crt)

        # check CA installed OS
        if not Ca.check_crt(CA_OS_PATH):
            utils.copy(ca_crt, CA_OS_PATH)

        # check CA installed to /etc
        if not Ca.check_crt(CA_ETC_PATH):
            utils.etc_install()

    def make_ca_crt(self):
        ca_key = self.ca_key
        ca_crt = self.ca_crt
        utils.subproc(msg=f'Make CA crt {ca_crt}', run=[
            'openssl', 'req', '-x509', '-new', '-nodes', '-sha256',
            '-days', '10000',
            '-subj', '/CN=First Galactic Empire/O=Death Star/OU=New Order IT Dept',
            '-key', ca_key,
            '-out', ca_crt
        ], exit_on_fail=True)


class Nss():
    @staticmethod
    def check_cert(nss_dir, cert_name=NSS_CERT_NAME):
        return utils.subproc(msg=f'Check NSS contains `{cert_name}` {nss_dir}', run=['certutil', '-V', '-n', cert_name, '-u', 'V', '-d', nss_dir])

    @staticmethod
    def install_cert(nss_dir, crt, cert_name=NSS_CERT_NAME):
        utils.subproc(msg=f'Copy CA -> browser DB {crt} -> {nss_dir}', run=['certutil', '-A', '-n', cert_name, '-t', 'TC,C,T', '-d', nss_dir, '-i', crt], exit_on_fail=True)

    def __init__(self, ca_crt=CA_CRT, nss_name=NSS_NAME, nss_dirs=NSS_DIRS):
        self.ca_crt = ca_crt
        self.nss_name = nss_name
        self.nss_dirs = nss_dirs

    def find(self):
        found_nss_dirs = []
        for nss_dir in self.nss_dirs:
            for root, _dirs, files in os.walk(nss_dir):
                if self.nss_name in files:
                    found_nss_dirs.append(root)
        return found_nss_dirs

    def install_ca(self):
        print('Search NSS - ', end='')
        found_nss_dirs = self.find()
        print(str(found_nss_dirs) + ' ok' if found_nss_dirs else 'not found')
        if not found_nss_dirs:
            print('Browser certificates DB not found. Browsers will not trust your https')
            return False
        for nss_dir in found_nss_dirs:
            if not Nss.check_cert(nss_dir=nss_dir):
                Nss.install_cert(nss_dir=nss_dir, crt=self.ca_crt)
        return True

class Cert():
    def __init__(self, ca=None, cert_list=CERT_LIST, csr=CERT_CSR, key=CERT_KEY, crt=CERT_CRT):
        self.ca = ca
        self.cert_list = cert_list
        self.csr = csr
        self.key = key
        self.crt = crt
        os.makedirs(CERT_LIST, exist_ok=True)

    def list_domains(self):
        cert_list = self.cert_list
        domain_names = sorted(listdir(cert_list))
        return domain_names

    def add_domain(self, name):
        cert_list = self.cert_list
        domain_file = os.path.join(cert_list, name)
        open(domain_file, 'a').close()
        utils.set_real_owner(domain_file)

    def delete_domain(self, name):
        cert_list = self.cert_list
        domain_file = os.path.join(cert_list, name)
        if isfile(domain_file):
            os.remove(domain_file)
        else:
            sys.exit(f'File not found {domain_file}')

    def issue_csr_key(self):
        csr = self.csr
        key = self.key
        utils.subproc(msg=f'Issue csr {csr} and key {key}', run=[
            'openssl', 'req', '-newkey', 'rsa:2048', '-nodes',
            '-keyout', key,
            '-subj', '/CN=Outer Rim/O=Tatooine/OU=Skywalker Ltd',
            '-out', csr
        ], exit_on_fail=True)
        utils.set_real_owner(csr)
        utils.set_real_owner(key)

    def issue_cert(self):
        ca_key = self.ca.ca_key
        ca_crt = self.ca.ca_crt
        csr = self.csr
        crt = self.crt
        cert_list = self.cert_list

        all_domains = ['DNS:' + fqdn for fqdn in listdir(cert_list)]
        san_str = ','.join(all_domains)
        san_file = f'{SW_HOME}/san'
        with open(san_file, 'w') as san:
            san.write(f'subjectAltName={san_str}')

        utils.subproc(msg='Make certificate', run=[
            'openssl', 'x509', '-req', '-extfile', san_file,
            '-CAcreateserial',
            '-days', '10000',
            '-CA', ca_crt,
            '-CAkey', ca_key,
            '-in', csr,
            '-out', crt
        ], exit_on_fail=True)
        os.remove(san_file)
        utils.set_real_owner(crt)
        utils.set_real_owner(CA_SRL)


class Nginx():
    @staticmethod
    def restart():
        utils.subproc(msg='Check nginx', run=['nginx', '-t'], exit_on_fail=True)
        utils.subproc(msg='Reload nginx', run=['service', 'nginx', 'reload'], exit_on_fail=True)
