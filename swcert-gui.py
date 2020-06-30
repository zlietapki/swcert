#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import GLib

import sys
import threading
import time

from swcertificate import Ca, Cert, Nginx, Nss
from swcertificate.gtkutils import TreeViewUtils
from swcertificate.settings import NGINX_KEY, NGINX_CRT, GLADE_MAIN_WINDOW
from swcertificate import utils


def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()

    return wrapper


class Handlers:
    def __init__(self, builder):
        self.builder = builder

        self.domains_lst = self.builder.get_object('domains_lst')
        self.entry = self.builder.get_object('domain_entry')
        self.restart_nginx = self.builder.get_object('restart_nginx')
        self.message_widget = self.builder.get_object('message_widget')
        self.message_label = self.builder.get_object('message_label')

        self.selected_iter = None

        self.color_black = '#000000'

    def main_window_delete_event(self, _widget, _event):
        Gtk.main_quit()

    def set_selected(self, selection):
        selected_iter = selection.get_selected()[1]
        if selected_iter:
            self.selected_iter = selected_iter
            domain_name = TreeViewUtils.get_record(self.domains_lst, selected_iter)
        else:
            domain_name = ''
        self.entry.set_placeholder_text(domain_name)

    def add_domain(self, _widget):
        domain_name = self.entry.get_text().strip()
        if domain_name:
            TreeViewUtils.add_record(self.domains_lst, [domain_name])
        else:
            self.display_message(self.color_black, 'Enter domain name')
        self.entry.set_text('')

    def remove_domain(self, _widget):
        selected_iter = self.selected_iter
        TreeViewUtils.delete_record(self.domains_lst, selected_iter)

    def save(self, _widget):
        self.add_domain(None)  # add entered but not added domain
        widget_domains = TreeViewUtils.get_records(self.domains_lst)
        if not widget_domains:
            return

        ca = setup_ca()

        cert = Cert()
        # delete all domains
        existing_domains = cert.list_domains()
        for domain in existing_domains:
            cert.delete_domain(domain)

        for domain in widget_domains:
            cert.add_domain(domain)
        cert = issue_cert(ca)
        popup_msg = 'Certificate saved'
        if self.restart_nginx.get_active():
            try:
                setup_nginx(cert)
            except RuntimeError as e:
                self.display_message(self.color_black, "Can't update Nginx\n" + str(e))
                return
            popup_msg += '\nNginx reloaded'
        self.display_message(self.color_black, popup_msg)

    def display_message(self, color, text):
        markup = f'<span foreground="{color}">{text}</span>'
        self.message_label.set_markup(markup)
        self.message_widget.popup()
        self.hide_message_timed()

    @threaded
    def hide_message_timed(self):
        time.sleep(3)
        GLib.idle_add(self.message_widget.popdown)


class MainWindow(Gtk.Window):
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file(GLADE_MAIN_WINDOW)
        self.builder.connect_signals(Handlers(builder=self.builder))
        self.builder.get_object('main_window').show()

        self.set_domains_list('domains_lst')

    def set_domains_list(self, treeview_id):
        domains_lst = self.builder.get_object(treeview_id)

        TreeViewUtils.add_column_text(domains_lst, title='Trusted domains')
        model = TreeViewUtils.set_model(domains_lst)

        all_domains = Cert().list_domains()
        for domain_name in all_domains:
            model.append([domain_name])


def setup_ca():
    # check CA key/crt or make new
    ca = Ca()
    ca.find_or_new_ca_key()
    ca.find_or_new_ca_crt()

    # setup NSS
    ca_serial = Ca.get_crt_serial(ca.ca_crt)
    if not utils.is_installed('certutil'):
        sys.exit('Install `certutil` be your self.\nUbuntu ex.\n\tsudo apt install libnss3-tools\nOr browsers will not '
                 'trust your https')

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
    return ca


def issue_cert(ca):
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
    MainWindow()
    Gtk.main()
