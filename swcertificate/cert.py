import os
import os.path
import sys

from . import utils
from .settings import CA_SRL, CERT_CRT, CERT_CSR, CERT_KEY, CERT_LIST, SW_HOME


class Cert():
    def __init__(self, ca=None, cert_list=CERT_LIST, csr=CERT_CSR, key=CERT_KEY, crt=CERT_CRT):
        self.ca = ca
        self.cert_list = cert_list
        self.csr = csr
        self.key = key
        self.crt = crt
        os.makedirs(CERT_LIST, exist_ok=True)
        utils.set_real_owner(CERT_LIST)

    def list_domains(self):
        cert_list = self.cert_list
        domain_names = sorted(os.listdir(cert_list))
        return domain_names

    def add_domain(self, name):
        cert_list = self.cert_list
        domain_file = os.path.join(cert_list, name)
        open(domain_file, 'a').close()
        utils.set_real_owner(domain_file)

    def delete_domain(self, name):
        cert_list = self.cert_list
        domain_file = os.path.join(cert_list, name)
        if os.path.isfile(domain_file):
            os.remove(domain_file)
        else:
            sys.exit(f'File not found {domain_file}')

    def issue_csr_key(self):
        csr = self.csr
        key = self.key
        utils.subproc(run=[
            'openssl', 'req', '-newkey', 'rsa:2048', '-nodes',
            '-keyout', key,
            '-subj', '/CN=Outer Rim/O=Tatooine/OU=Skywalker Ltd',
            '-out', csr
        ], msg=f'Issue csr {csr} and key {key}', exit_on_fail=True)
        utils.set_real_owner(csr)
        utils.set_real_owner(key)

    def issue_cert(self):
        ca_key = self.ca.ca_key
        ca_crt = self.ca.ca_crt
        csr = self.csr
        crt = self.crt
        cert_list = self.cert_list

        all_domains = ['DNS:' + fqdn for fqdn in os.listdir(cert_list)]
        san_str = ','.join(all_domains)
        san_file = f'{SW_HOME}/san'
        with open(san_file, 'w') as san:
            san.write(f'subjectAltName={san_str}')

        utils.subproc(run=[
            'openssl', 'x509', '-req', '-extfile', san_file,
            '-CAcreateserial',
            '-days', '10000',
            '-CA', ca_crt,
            '-CAkey', ca_key,
            '-in', csr,
            '-out', crt
        ], msg='Make certificate', exit_on_fail=True)
        os.remove(san_file)
        utils.set_real_owner(crt)
        utils.set_real_owner(CA_SRL)
