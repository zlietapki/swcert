from . import utils


class Nginx():
    @staticmethod
    def restart():
        utils.subproc(run=['nginx', '-t'], msg='Check nginx', exit_on_fail=True)
        utils.subproc(run=['service', 'nginx', 'reload'], msg='Reload nginx', exit_on_fail=True)
