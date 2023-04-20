import click
import os
import netifaces
import http.server
import socketserver
from pyNfsClient import (Portmap, Mount, NFSv3, MNT3_OK, NFS_PROGRAM,NFS_V3, NFS3_OK, DATA_SYNC)
from pyftpdlib.handlers import FTPHandler, ThrottledDTPHandler
from pyftpdlib.servers import FTPServer as FTPS
from pyftpdlib.authorizers import DummyAuthorizer

class NotRequiredIf(click.Option):
    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop('not_required_if')
        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs['help'] = (kwargs.get('help', '') +
            ' NOTE: This argument is mutually exclusive with %s' %
            self.not_required_if
        ).strip()
        super(NotRequiredIf, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        we_are_present = self.name in opts
        other_present = self.not_required_if in opts

        if other_present:
            if we_are_present:
                raise click.UsageError(
                    "Illegal usage: `%s` is mutually exclusive with `%s`" % (
                        self.name, self.not_required_if))
            else:
                self.prompt = None

        return super(NotRequiredIf, self).handle_parse_result(
            ctx, opts, args)

class FileServer:
    def __init__(self, lport, lhost='', username="anonymous", password="anonymous"):
        self.lport = lport
        self.lhost = lhost
        self.username = username
        self.password = password

    def start_server(self):
        make_generated_directory()
        os.chdir(GENERATED_SHELLS)


    def print_start(self):
        click.echo(f"Starting {self.__class__.__name__} on {self.lhost}:{self.lport}")

    def print_exit(self):
        click.echo(f"Closing {self.__class__.__name__} on {self.lhost}:{self.lport}")

    def __enter__(self):
        pass

    def __exit__(self, exec_type, exec_value, exec_traceback):
        self.print_exit()

    def serve_until_interrupt(self, httpd):
        try:
            self.print_start()
            httpd.serve_forever()
        except KeyboardInterrupt:
            click.echo("KeyboardInterrupt: Shutting Server Down")
        
class HTTPServer(FileServer):
    SERVER_NAME = "http"
    def __init__(self, lport):
        FileServer.__init__(self, lport)

    def __enter__(self):
        FileServer.start_server(self)
        handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer((self.lhost, self.lport), handler)
        FileServer.serve_until_interrupt(self, httpd)

class FTPServer(FileServer):
    SERVER_NAME = "ftp"
    def __init__(self, lport):
        FileServer.__init__(self, lport)

    def __enter__(self):
        FileServer.start_server(self)
        authorizer = DummyAuthorizer()
        authorizer.add_user(self.username, self.password, os.getcwd(), perm='elradfmw')
        handler = FTPHandler
        handler.authorizer = authorizer
        handler.banner = "pyftplibd based ftpd ready"
        address = (self.lhost, self.lport)
        server = FTPS(address, handler)
        server.max_cons = 256
        server.max_cons_per_ip = 5
        FileServer.serve_until_interrupt(self, server)


class NFSServer(FileServer):
    pass

class SMBServer(FileServer):
    pass


        

# return all shell commands
def get_all_options(path):
    raw_shells = os.listdir(path=path)
    return [os.path.splitext(language)[0] for language in raw_shells]


def load(shell_directory, command):
    try:
        command_path = f"{shell_directory}/{command}.txt"
        with click.open_file(command_path, "r") as f:
            return f.read()
    except:
        raise click.UsageError("Shell path not found")

def inject(shell, lhost, lport):
    return shell.format(lhost=lhost, lport=lport)


def mutually_exclusive(arg1, arg2, exception):
    if not bool(arg1) ^ bool(arg2):
        raise exception

    elif arg1:
        return 0
    elif arg2:
        return 1

# handle lhost inputs
def get_ip(ip, interface):
    active_arg = mutually_exclusive(ip, interface, click.BadParameter("Must enter ip or interface"))
    match active_arg:
        case 0:
            return ip
        case 1:
            return netifaces.ifaddresses(interface)[2][0]["addr"]
    return None
    

def get_shell(template, shell, shell_dir):
    active_arg = mutually_exclusive(template, shell, click.BadParameter("Must enter a shell or template"))
    match active_arg:
        case 0:
            return template.read()
        case 1:
            return load(shell_dir, shell)
    return (None, None)
        
def make_generated_directory():
    if not os.path.isdir(GENERATED_SHELLS):
        os.mkdir(GENERATED_SHELLS)

def get_extension(extension, language, command_extensions):
    active_arg = mutually_exclusive(extension, language, click.BadParameter("Must enter an extension or language"))
    match active_arg:
        case 0:
            return extension
        case 1:
            return command_extensions[language]
    return None


def create_shell(reverse_shell, output):
    if not output:
        click.echo(reverse_shell)
        return
    output.write(reverse_shell)
    click.echo("Shell Generated Successfully")

def listen_on(listen, port):
    if not listen:
        return None

    for Server in SUPPORTED_FILE_SERVERS:
        if Server.SERVER_NAME == listen:
            with Server(port):
                pass



# path to reverse shells
SUPPORTED_FILE_SERVERS = [HTTPServer, FTPServer]
FILE_CWD = os.path.dirname(os.path.realpath(__file__))
SHELL_PATH = os.path.join(FILE_CWD, "template_shells")
SHELL_TEMPLATES = get_all_options(SHELL_PATH)
SYSTEM_INTERFACES = netifaces.interfaces()
GENERATED_SHELLS = "generated_shells"
# bash.txt  groovy.txt  java.txt  netcat.txt  perl.txt  php.txt  python.txt  ruby.txt  telnet.txt  xterm.txt
COMMAND_EXTENSIONS = {
    "bash": "sh", 
    "groovy": "groovy", 
    "java": "java",
    "netcat": "txt",
    "perl": "pl",
    "php": "php",
    "python": "py",
    "ruby": "rb",
    "telnet": "txt",
    "xterm": "txt",
}

# main command
@click.command()
@click.option(
    "-s",
    "--shell",
    "shell",
    type=click.Choice(SHELL_TEMPLATES),
    cls=NotRequiredIf,
    not_required_if="template",
    prompt=True
)
@click.option(
        "-t",
        "--template",
        "template",
        type=click.File("r"),
        cls=NotRequiredIf,
        not_required_if="shell",
        prompt=True
        )
@click.option("-i", "--ip", "ip", type=str, cls=NotRequiredIf, not_required_if="interface")
@click.option(
    "-I",
    "--interface",
    "interface",
    type=click.Choice(SYSTEM_INTERFACES),
    cls=NotRequiredIf,
    not_required_if="ip"
)
@click.option("-l", "--listen", "listen", type=click.Choice([server.SERVER_NAME for server in SUPPORTED_FILE_SERVERS]))
@click.option("-o", "--output", "output", type=click.File("w"))
@click.argument("port", type=int)
def generate(shell, template, ip, interface, listen, output, port):
    raw_shell = get_shell(template, shell, SHELL_PATH)
    lhost = get_ip(ip, interface)
    reverse_shell = inject(raw_shell, lhost, port)
    create_shell(reverse_shell, output)
    listen_on(listen, port)


if __name__ == "__main__":
    generate()
