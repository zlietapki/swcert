SWCert
======

Browser trusted self signed certificate for localhost and any other domain without warnings from browser  
Auto check and install CA for browsers  
Auto update Nginx certificate  

Install
-------

```bash
sudo apt install libnss3-tools python3-gi -y
git clone git@github.com:zlietapki/swcert.git ~/.swcert
sudo ln -s -f ~/.swcert/swcert.py /usr/local/bin/swcert
sudo ln -s -f ~/.swcert/swcert-gui.py /usr/local/bin/swcert-gui
```

Usage
-----

```bash
sudo swcert-gui
sudo swcert localhost somehost.lan *.somehost.lan
```

Windows host with Linux virtualbox
----------------------------------

Root CA should be installed manually for Windows browsers  
Copy `~/.swcert/ca/swcert_CA.crt` from Linux

### Chrome

<chrome://settings/certificates> -> Authorities -> Import -> swcert_CA.crt  

### Firefox

<about:preferences#privacy> -> View ceritificates -> Authorities -> Import -> swcert_CA.crt  
