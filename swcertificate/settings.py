import os
import pwd

real_uid = int(os.environ.get('SUDO_UID', os.getuid()))
USER_HOME = pwd.getpwuid(real_uid).pw_dir

SW_HOME = os.path.join(USER_HOME, '.swcert')  # projects home
# SW_HOME = '/home/asd/workspace/swcert'
CA_HOME = os.path.join(SW_HOME, 'ca')
CA_KEY = os.path.join(CA_HOME, 'swcert_CA.key')
CA_CRT = os.path.join(CA_HOME, 'swcert_CA.crt')

NSS_DIRS = [  # find for browser CA database here
    os.path.join(USER_HOME, '.pki'),
    os.path.join(USER_HOME, '.mozilla'),
]
NSS_NAME = 'cert9.db'  # browser DB filename
NSS_CERT_NAME = 'swcert'  # install your new CA cert this name

CA_SRL = os.path.join(SW_HOME, 'ca/swcert_CA.srl')
CA_OS_PATH = '/usr/local/share/ca-certificates/extra/swcert_CA.crt'
CA_ETC_PATH = '/etc/ssl/certs/swcert_CA.pem'  # .pem not .crt!

CERT_HOME = os.path.join(SW_HOME, 'cert')
CERT_CSR = os.path.join(CERT_HOME, 'swcert.csr')
CERT_KEY = os.path.join(CERT_HOME, 'swcert.key')
CERT_CRT = os.path.join(CERT_HOME, 'swcert.crt')
CERT_LIST = os.path.join(CERT_HOME, 'list.d')  # domains list as filenames

NGINX_USE = True  # copy new certificate for nginx and reload nginx every time
NGINX_KEY = '/etc/swcert/swcert.key'
NGINX_CRT = '/etc/swcert/swcert.crt'

GLADE_MAIN_WINDOW = os.path.join(SW_HOME, 'glade/main.glade')
