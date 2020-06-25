#!/usr/bin/env python3
import sys
from os.path import basename

from swcertificate import Ca, Cert, Nginx, Nss
from swcertificate.settings import NGINX_CRT, NGINX_KEY, NGINX_USE
from swcertificate import utils


# pylint: disable=pointless-string-statement
'''
Install
git clone git@github.com:zlietapki/swcert.git ~/.swcert
sudo ln -s ~/.swcert/swcert.py /usr/local/bin/swcert

Usage:
swcert localhost
'''

def usage():
    msg = 'Usage:\n'
    msg += f'\t{basename(__file__)} <domain_name> [<domain_name>...] - trust domain\n'
    msg += f'\t{basename(__file__)} -d <domain_name> [<domain_name>...] - forget domain\n'
    sys.exit(msg)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()

    if sys.argv[1] == '-d':
        if len(sys.argv) < 3:
            usage()

        for domain_name in sys.argv[2:]:
            print(f'Remove domain `{domain_name}` from certificate subj list')
            Cert().delete_domain(domain_name)
    elif sys.argv[1] == '--list':
        domain_names = Cert().list_domains()
        print(*domain_names, sep='\n')
        sys.exit()
    else:
        for domain_name in sys.argv[1:]:
            print(f'Add domain `{domain_name}` to certificate subj list')
            Cert().add_domain(domain_name)

    # check CA key/crt or make new
    ca = Ca()
    ca.find_or_new_ca_key()
    ca.find_or_new_ca_crt()

    # setup NSS
    ca_serial = Ca.get_crt_serial(ca.ca_crt)
    if not utils.is_installed('certutil'):
        sys.exit('Install `certutil` be your self.\nUbuntu ex.\n\tsudo apt install libnss3-tools\nBrowsers will not trust your https')

    found_nss_dirs = Nss.find()
    if not found_nss_dirs:
        sys.exit('NSS dirs not found\nBrowsers will not trust your https')
    for nss_dir in found_nss_dirs:
        nss_ca_serial = Nss.get_crt_serial(nss_dir)
        if not nss_ca_serial:
            Nss.install_ca(nss_dir)
        elif nss_ca_serial != ca_serial:
            Nss.delete_cert(nss_dir)
            Nss.install_ca(nss_dir)

    # issue cert
    cert = Cert(ca)
    cert.issue_csr_key()
    cert.issue_cert()

    # install cert to nginx
    if NGINX_USE:
        if utils.is_installed('nginx'):
            utils.copy(cert.key, NGINX_KEY)
            utils.copy(cert.crt, NGINX_CRT)

            Nginx.restart()
            print('Dont forget edit nginx config')
            print('\tlisten 443 ssl http2;')
            print(f'\tssl_certificate_key {NGINX_KEY};')
            print(f'\tssl_certificate {NGINX_CRT};')
        else:
            print('`Nginx` is not installed. Skip install Nginx certificates')
