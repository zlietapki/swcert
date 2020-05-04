#!/usr/bin/env python3
import os.path
import pwd
import shutil
import subprocess
import sys
from os import listdir
from os.path import basename, dirname, isfile

'''
Install
git clone github ~/swcert
sudo ln -s ~/swcert/swcert.py /usr/local/bin/swcert

Usage:
swcert localhost
'''

real_uid = int(os.environ.get('SUDO_UID', os.getuid()))
USER_HOME = pwd.getpwuid(real_uid).pw_dir

NSS_DIRS = [  # find for browser CA database here
    os.path.join(USER_HOME, '.pki'),
    os.path.join(USER_HOME, '.mozilla'),
]
NSS_NAME = 'cert9.db'  # browser DB filename
NSS_CERT_NAME = 'swcert'  # install your new CA cert this name

SW_HOME = os.path.join(USER_HOME, 'swcert')  # projects home

CA_KEY = os.path.join(SW_HOME, 'ca/swcert_CA.key')
CA_CRT = os.path.join(SW_HOME, 'ca/swcert_CA.crt')
CA_OS_PATH = '/usr/local/share/ca-certificates/extra/swcert_CA.crt'
CA_ETC_PATH = '/etc/ssl/certs/swcert_CA.pem'  # .pem not .crt!

CERT_CSR = os.path.join(SW_HOME, 'cert/swcert.csr')
CERT_KEY = os.path.join(SW_HOME, 'cert/swcert.key')
CERT_CRT = os.path.join(SW_HOME, 'cert/swcert.crt')
CERT_LIST = os.path.join(SW_HOME, 'cert/list.d')  # domains list as filenames

NGINX_USE = True  # copy new certificate for nginx and restart nginx every time
NGINX_KEY = '/etc/nginx/ssl/swcert.key'
NGINX_CRT = '/etc/nginx/ssl/swcert.crt'


def check_key(key):
    print(f'Check CA key {key} - ', end='')
    try:
        subprocess.run(['openssl', 'rsa', '-check', '-in', key], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print('err')
        return False
    print('ok')
    return True


def make_ca_key(key):
    print(f'Make CA key {key} - ', end='')
    try:
        subprocess.run(['openssl', 'genrsa', '-out', key], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print('err')
        sys.exit(e.stderr.decode('utf-8'))
    print('ok')
    return True


def check_crt(crt):
    print(f'Check CA crt {crt} - ', end='')
    try:
        subprocess.run(['openssl', 'x509', '-text', '-noout', '-in', crt], check=True, capture_output=True)  # check crt
    except subprocess.CalledProcessError:
        print('err')
        return False
    print('ok')
    return True


def make_ca_crt(crt, key):
    try:
        print(f'Make CA crt {crt} - ', end='')
        subprocess.run([
            'openssl', 'req', '-x509', '-new', '-nodes', '-sha256',
            '-days', '10000',
            '-subj', '/CN=First Galactic Empire/O=Death Star/OU=New Order IT Dept',
            '-key', key,
            '-out', crt
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print('err')
        sys.exit(e.stderr.decode('utf-8'))
    print('ok')
    return True


def copy(src, dst):
    dst_dir = dirname(dst)
    try:
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        shutil.copyfile(src, dst)
    except PermissionError as e:
        sys.exit(e.strerror + '. Run with `sudo`')
    return True


def etc_install():
    # install to /etc
    print('Update /etc/ssl/certs/ - ', end='')
    try:
        subprocess.run(['update-ca-certificates', '--fresh'], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print('err')
        sys.exit(e.stderr.decode('utf-8'))
    print('ok')


def nss_find(nss_name, nss_dirs):
    print('Find browsers cert DB - ', end='')
    nss = []
    for nss_dir in nss_dirs:
        print(f'{nss_dir} ', end='')
        for root, _dirs, files in os.walk(nss_dir):
            if nss_name in files:
                nss.append(root)
    if nss:
        print(nss, ' ok')
    else:
        print('not found')
    return nss


def check_nss(nss, cert_name=NSS_CERT_NAME):
    print(f'Check browser DB `{cert_name}` {nss} - ', end='')
    try:
        subprocess.run(['certutil', '-V', '-n', cert_name, '-u', 'V', '-d', nss], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print('err')
        return False
    print('ok')
    return True


def nss_install(nss, crt, cert_name=NSS_CERT_NAME):
    print(f'Copy CA -> browser DB {crt} -> {nss} - ', end='')
    try:
        subprocess.run(['certutil', '-A', '-n', cert_name, '-t', 'TC,C,T', '-d', nss, '-i', crt], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print('err')
        sys.exit(e.stderr.decode('utf-8'))
    print('ok')


def add_domain(domain, cert_list=CERT_LIST):
    print(f'Add `{domain}` to certificate subj list - ', end='')
    domain_file = os.path.join(cert_list, domain)
    open(domain_file, 'a').close()
    print('ok')
    return True


def delete_domain(domain, cert_list=CERT_LIST):
    print(f'Remove `{domain}` from certificate subj list - ', end='')
    domain_file = os.path.join(cert_list, domain)
    if isfile(domain_file):
        os.remove(domain_file)
        print('ok')
    else:
        print('err')
    return True


def issue_cert(ca_key=CA_KEY, ca_crt=CA_CRT, cert_csr=CERT_CSR, cert_key=CERT_KEY, cert_crt=CERT_CRT, cert_list=CERT_LIST):
    all_domains = ['DNS:' + fqdn for fqdn in listdir(cert_list)]
    san_str = ','.join(all_domains)
    san_file = f'{SW_HOME}/san'
    with open(san_file, 'w') as san:
        san.write(f'subjectAltName={san_str}')

    print('Make certificate key and csr - ', end='')
    try:
        subprocess.run([
            'openssl', 'req', '-newkey', 'rsa:2048', '-nodes',
            '-keyout', cert_key,
            '-subj', '/CN=Outer Rim/O=Tatooine/OU=Skywalker Ltd',
            '-out', cert_csr
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print('err')
        sys.exit(e.stderr.decode('utf-8'))
    print('ok')

    print('Make certificate - ', end='')
    try:
        subprocess.run([
            'openssl', 'x509', '-req', '-extfile', san_file,
            '-CAcreateserial',
            '-days', '10000',
            '-CA', ca_crt,
            '-CAkey', ca_key,
            '-in', cert_csr,
            '-out', cert_crt
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print('err')
        sys.exit(e.stderr.decode('utf-8'))
    print('ok')
    return True


def restart_nginx():
    print('Restart nginx - ', end='')
    try:
        subprocess.run(['service', 'nginx', 'restart'], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print('err')
        sys.exit(e.stderr.decode('utf-8'))
    print('ok')


def usage():
    msg = 'Usage:\n'
    msg += f'\t{basename(__file__)} <domain_name> [<domain_name>...] - trust domain\n'
    msg += f'\t{basename(__file__)} -d <domain_name> [<domain_name>...] - forget domain\n'
    sys.exit(msg)


def main():
    # check CA key/crt or make new
    if not check_key(CA_KEY):
        make_ca_key(CA_KEY)
    if not check_crt(CA_CRT):
        make_ca_crt(CA_CRT, CA_KEY)

    # check CA installed OS
    if not check_crt(CA_OS_PATH):
        print(f'Copy {CA_CRT} -> {CA_OS_PATH} - ', end='')
        copy(CA_CRT, CA_OS_PATH)
        print('ok')

    # check CA installed to /etc
    if not check_crt(CA_ETC_PATH):
        etc_install()

    # check certutil installed
    certutil_installed = False
    print('Check `certutil` installed - ', end='')
    try:
        subprocess.run(['which', 'certutil'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print('err')
        sys.exit('Browsers will not trust your https\nInstall `certutil` be your self.\nUbuntu ex.\n\tsudo apt install libnss3-tools')
    print('ok')
    certutil_installed = True

    # install CA to browsers DB
    if certutil_installed:
        nss_list = nss_find(NSS_NAME, NSS_DIRS)
        if not nss_list:
            sys.exit('Browser certificates DB not found. Browsers will not trust your https')
        for nss in nss_list:
            if not check_nss(nss=nss):
                nss_install(nss=nss, crt=CA_CRT)

    # add/remove domain from cert list
    if sys.argv[1] != '-d':
        for domain in sys.argv[1:]:
            add_domain(domain)
    else:
        for domain in sys.argv[2:]:
            delete_domain(domain)

    issue_cert()

    # check nginx installed
    nginx_installed = False
    try:
        subprocess.run(['which', 'nginx'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print('`Nginx` is not installed. Skip install Nginx certificates')
    else:
        nginx_installed = True

    if nginx_installed and NGINX_USE:
        # copy cert and key to nginx
        print(f'Install nginx cert key {CERT_KEY} -> {NGINX_KEY} - ', end='')
        copy(CERT_KEY, NGINX_KEY)
        print('ok')

        print(f'Install nginx certificate {CERT_CRT} -> {NGINX_CRT} - ', end='')
        copy(CERT_CRT, NGINX_CRT)
        print('ok')

        restart_nginx()
        print('Dont forget edit nginx config')
        print('\tlisten 443 ssl http2;')
        print(f'\tssl_certificate_key {NGINX_KEY};')
        print(f'\tssl_certificate {NGINX_CRT};')


if __name__ == '__main__':
    # check params
    if len(sys.argv) < 2:
        usage()
    if sys.argv[1] == '-d' and len(sys.argv) < 3:
        usage()
    main()
