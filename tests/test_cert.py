import os
import os.path

import pytest

from swcertificate import Ca, Cert


class TestListDomains:
    def test_ok(self, tmpdir):
        domain1 = os.path.join(tmpdir, 'domain')
        open(domain1, 'a').close()
        domain2 = os.path.join(tmpdir, '*.domain')
        open(domain2, 'a').close()
        domain3 = os.path.join(tmpdir, '*.domain.some')
        open(domain3, 'a').close()

        cert = Cert(cert_list=tmpdir)
        names = cert.list_domains()
        assert 'domain' in names
        assert '*.domain' in names
        assert '*.domain.some' in names

    def test_no_path(self, tmpdir):
        cert = Cert(cert_list=tmpdir)
        names = cert.list_domains()
        assert not names


class TestAddDomain:
    def test_ok(self, tmpdir):
        cert = Cert(cert_list=tmpdir)
        cert.add_domain('some')
        names = cert.list_domains()
        assert 'some' in names


class TestDeleteDomain:
    def test_ok(self, tmpdir):
        cert = Cert(cert_list=tmpdir)
        cert.add_domain('some')
        names = cert.list_domains()
        assert 'some' in names

        cert.delete_domain('some')
        names = cert.list_domains()
        assert not 'some' in names

    def test_not_found(self, tmpdir):
        cert = Cert(cert_list=tmpdir)

        with pytest.raises(SystemExit) as excinfo:
            cert.delete_domain('some')
        assert 'File not found' in excinfo.value.code


class TestIssueCsrKey:
    def test_ok(self, tmpdir):
        csr = os.path.join(tmpdir, 'some.csr')
        key = os.path.join(tmpdir, 'some.key')
        cert = Cert(csr=csr, key=key)
        cert.issue_csr_key()
        assert os.path.isfile(csr)
        assert os.path.isfile(key)


class TestIssueCert:
    def test_ok(self, tmpdir):
        ca_key = os.path.join(tmpdir, 'ca.key')
        ca_crt = os.path.join(tmpdir, 'ca.crt')
        ca = Ca(ca_key=ca_key, ca_crt=ca_crt)
        ca.make_ca_key()
        ca.make_ca_crt()

        csr = os.path.join(tmpdir, 'some.csr')
        key = os.path.join(tmpdir, 'some.key')
        crt = os.path.join(tmpdir, 'some.crt')

        cert_list = os.path.join(tmpdir, 'domains_list')
        os.makedirs(cert_list)

        cert = Cert(ca=ca, csr=csr, key=key, crt=crt, cert_list=cert_list)
        cert.add_domain('domainame')
        cert.issue_csr_key()
        cert.issue_cert()
        assert os.path.isfile(crt)
