import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import sys

from swcertificate import Ca, Cert, Nginx, Nss
from swcertificate.gtkutils import TreeViewUtils
from swcertificate.settings import NGINX_KEY, NGINX_CRT
from swcertificate import utils

class Handlers():
    def __init__(self, builder):
        self.builder = builder

        self.domains_lst = self.builder.get_object('domains_lst')
        self.entry = self.builder.get_object('domain_entry')
        self.restart_nginx = self.builder.get_object('restart_nginx')
        self.selected_iter = None

    def main_window_delete_event(self, _widget, _event):
        Gtk.main_quit()

    def set_selected(self, selection):
        selected_iter = selection.get_selected()[1]
        if selected_iter:
            self.selected_iter = selected_iter

            domain_name = TreeViewUtils.get_record(self.domains_lst, selected_iter)
            self.entry.set_placeholder_text(domain_name)

    def add_domain(self, _widget):
        domain_name = self.entry.get_text().strip()
        if domain_name:
            TreeViewUtils.add_record(self.domains_lst, [domain_name])
        self.entry.set_text('')

    def remove_domain(self, _widget):
        selected_iter = self.selected_iter
        TreeViewUtils.delete_record(self.domains_lst, selected_iter)

    def save(self, _widget):
        widget_domains = TreeViewUtils.get_records(self.domains_lst)
        cert = Cert()
        # delete all domains
        existing_domains = cert.list_domains()
        for domain in existing_domains:
            cert.delete_domain(domain)

        for domain in widget_domains:
            cert.add_domain(domain)
        cert = issue_cert()
        if self.restart_nginx.get_active():
            setup_nginx(cert)

class MainWindow(Gtk.Window):
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file('glade/main.glade')
        self.builder.connect_signals(Handlers(builder=self.builder))
        self.builder.get_object('main_window').show()

        self.set_domains_list('domains_lst')

    def set_domains_list(self, treeview_id):
        domains_lst = self.builder.get_object(treeview_id)

        TreeViewUtils.add_column_text(domains_lst, title='Domains')
        model = TreeViewUtils.set_model(domains_lst)

        all_domains = Cert().list_domains()
        for domain_name in all_domains:
            model.append([domain_name])

def issue_cert():
    cert = Cert(ca)
    cert.issue_csr_key()
    cert.issue_cert()
    return cert

def setup_nginx(cert):
    if not utils.is_installed('nginx'):
        return

    utils.copy(cert.key, NGINX_KEY)
    utils.copy(cert.crt, NGINX_CRT)
    Nginx.restart()


if __name__ == '__main__':
    # check CA key/crt or make new
    ca = Ca()
    ca.find_or_new_ca_key()
    ca.find_or_new_ca_crt()

    # setup nss
    if utils.is_installed('certutil'):
        nss = Nss(ca_crt=ca.ca_crt)
        nss.install_ca()
    else:
        sys.exit('Browsers will not trust your https\nInstall `certutil` be your self.\nUbuntu ex.\n\tsudo apt install libnss3-tools')

    MainWindow()
    Gtk.main()
