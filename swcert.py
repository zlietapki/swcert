#!/usr/bin/env python3
import os
import os.path
import pwd
import shutil
import subprocess
import sys
from os import listdir
from os.path import basename, dirname, isfile

'''
Install
git clone git@github.com:zlietapki/swcert.git ~/.swcert
sudo ln -s ~/.swcert/swcert.py /usr/local/bin/swcert

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

SW_HOME = os.path.join(USER_HOME, '.swcert')  # projects home

CA_KEY = os.path.join(SW_HOME, 'ca/swcert_CA.key')
CA_CRT = os.path.join(SW_HOME, 'ca/swcert_CA.crt')
CA_SRL = os.path.join(SW_HOME, 'ca/swcert_CA.srl')
CA_OS_PATH = '/usr/local/share/ca-certificates/extra/swcert_CA.crt'
CA_ETC_PATH = '/etc/ssl/certs/swcert_CA.pem'  # .pem not .crt!

CERT_CSR = os.path.join(SW_HOME, 'cert/swcert.csr')
CERT_KEY = os.path.join(SW_HOME, 'cert/swcert.key')
CERT_CRT = os.path.join(SW_HOME, 'cert/swcert.crt')
CERT_LIST = os.path.join(SW_HOME, 'cert/list.d')  # domains list as filenames

NGINX_USE = True  # copy new certificate for nginx and reload nginx every time
NGINX_KEY = '/etc/nginx/ssl/swcert.key'
NGINX_CRT = '/etc/nginx/ssl/swcert.crt'


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
        # print(err_msg)

        if exit_on_fail:
            sys.exit(err_msg)
        return False
    print(ok_msg)
    return True


def set_real_owner(path):
    owner = os.getlogin()
    shutil.chown(path, user=owner, group=owner)
    return owner


def check_ca_key(key=CA_KEY):
    return subproc(msg=f'Check CA key {key}', run=['openssl', 'rsa', '-check', '-in', key])


def make_ca_key(key=CA_KEY):
    return subproc(msg=f'Make CA key {key}', run=['openssl', 'genrsa', '-out', key], exit_on_fail=True)


def check_crt(crt=CA_CRT):
    return subproc(msg=f'Check CA crt {crt}', run=['openssl', 'x509', '-text', '-noout', '-in', crt])


def make_ca_crt(crt, key):
    return subproc(msg=f'Make CA crt {crt}', run=[
        'openssl', 'req', '-x509', '-new', '-nodes', '-sha256',
        '-days', '10000',
        '-subj', '/CN=First Galactic Empire/O=Death Star/OU=New Order IT Dept',
        '-key', key,
        '-out', crt
    ], exit_on_fail=True)


def copy(src, dst):
    print(f'Copy {src} -> {dst} - ', end='')
    dst_dir = dirname(dst)
    try:
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        shutil.copyfile(src, dst)
    except PermissionError as e:
        print('Error')
        sys.exit(e.strerror + '. Run with `sudo`')
    print('OK')
    return True


def etc_install():
    subproc(msg='Update /etc/ssl/certs/', run=['update-ca-certificates', '--fresh'], exit_on_fail=True)


def nss_find(nss_name, nss_dirs):
    print('Search NSS - ', end='')
    nss = []
    for nss_dir in nss_dirs:
        for root, _dirs, files in os.walk(nss_dir):
            if nss_name in files:
                nss.append(root)
    if nss:
        print(nss, ' ok')
    else:
        print('not found')
    return nss


def nss_check_cert(nss, cert_name=NSS_CERT_NAME):
    return subproc(msg=f'Check NSS contains `{cert_name}` {nss}', run=['certutil', '-V', '-n', cert_name, '-u', 'V', '-d', nss])


def nss_install_cert(nss, crt, cert_name=NSS_CERT_NAME):
    return subproc(msg=f'Copy CA -> browser DB {crt} -> {nss}', run=['certutil', '-A', '-n', cert_name, '-t', 'TC,C,T', '-d', nss, '-i', crt], exit_on_fail=True)


def add_domain(domain, cert_list=CERT_LIST):
    print(f'Add domain `{domain}` to certificate subj list - ', end='')
    domain_file = os.path.join(cert_list, domain)
    open(domain_file, 'a').close()
    print('ok')
    return True


def delete_domain(domain, cert_list=CERT_LIST):
    print(f'Remove domain `{domain}` from certificate subj list - ', end='')
    domain_file = os.path.join(cert_list, domain)
    if isfile(domain_file):
        os.remove(domain_file)
        print('ok')
    else:
        print('Error')
        sys.exit(f'File not found {domain_file}')
    return True


def issue_csr_key(csr=CERT_CSR, key=CERT_KEY):
    subproc(msg=f'Issue csr {csr} and key {key}', run=[
        'openssl', 'req', '-newkey', 'rsa:2048', '-nodes',
        '-keyout', key,
        '-subj', '/CN=Outer Rim/O=Tatooine/OU=Skywalker Ltd',
        '-out', csr
    ], exit_on_fail=True)


def issue_cert(ca_key=CA_KEY, ca_crt=CA_CRT, csr=CERT_CSR, cert_crt=CERT_CRT, cert_list=CERT_LIST):
    all_domains = ['DNS:' + fqdn for fqdn in listdir(cert_list)]
    san_str = ','.join(all_domains)
    san_file = f'{SW_HOME}/san'
    with open(san_file, 'w') as san:
        san.write(f'subjectAltName={san_str}')

    res = subproc(msg='Make certificate', run=[
        'openssl', 'x509', '-req', '-extfile', san_file,
        '-CAcreateserial',
        '-days', '10000',
        '-CA', ca_crt,
        '-CAkey', ca_key,
        '-in', csr,
        '-out', cert_crt
    ], exit_on_fail=True)
    os.remove(san_file)
    return res


def nginx_installed():
    return subproc(msg='Nginx installed', run=['which', 'nginx'])


def restart_nginx():
    subproc(msg='Check nginx', run=['nginx', '-t'], exit_on_fail=True)
    return subproc(msg='Restart nginx', run=['service', 'nginx', 'reload'], exit_on_fail=True)


def list_domains(cert_list=CERT_LIST):
    all_domains = sorted(listdir(cert_list))
    for domain in all_domains:
        print(domain)
    sys.exit()


def usage():
    msg = 'Usage:\n'
    msg += f'\t{basename(__file__)} <domain_name> [<domain_name>...] - trust domain\n'
    msg += f'\t{basename(__file__)} -d <domain_name> [<domain_name>...] - forget domain\n'
    sys.exit(msg)


def main():
    # check CA key/crt or make new
    if not check_ca_key():
        make_ca_key()
        set_real_owner(CA_KEY)
    if not check_crt(CA_CRT):
        make_ca_crt(CA_CRT, CA_KEY)
        set_real_owner(CA_CRT)

    # check CA installed OS
    if not check_crt(CA_OS_PATH):
        copy(CA_CRT, CA_OS_PATH)

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
            if not nss_check_cert(nss=nss):
                nss_install_cert(nss=nss, crt=CA_CRT)

    # add/remove domain from cert list
    if sys.argv[1] != '-d':
        for domain in sys.argv[1:]:
            add_domain(domain)
            set_real_owner(os.path.join(CERT_LIST, domain))
    else:
        for domain in sys.argv[2:]:
            delete_domain(domain)

    issue_csr_key(csr=CERT_CSR, key=CERT_KEY)
    set_real_owner(CERT_CSR)
    set_real_owner(CERT_KEY)

    issue_cert()
    set_real_owner(CERT_CRT)
    set_real_owner(CA_SRL)

    if NGINX_USE:
        if nginx_installed():
            # copy cert and key to nginx
            copy(CERT_KEY, NGINX_KEY)
            copy(CERT_CRT, NGINX_CRT)

            restart_nginx()
            print('Dont forget edit nginx config')
            print('\tlisten 443 ssl http2;')
            print(f'\tssl_certificate_key {NGINX_KEY};')
            print(f'\tssl_certificate {NGINX_CRT};')
        else:
            print('`Nginx` is not installed. Skip install Nginx certificates')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
    if sys.argv[1] == '-d' and len(sys.argv) < 3:
        usage()
    if sys.argv[1] == '--list':
        list_domains()
    main()
