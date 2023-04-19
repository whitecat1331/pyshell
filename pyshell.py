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
            print("KeyboardInterrupt: Shutting Server Down")
        
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

    finally:
        return None



def inject(shell, lhost, lport):
    return shell.format(lhost=lhost, lport=lport)

# only return one parameter or the other 
def get_exclusive(possible_parameters, exception):
    all_values = list(possible_parameters.values())
    if not bool(all_values[0]) ^ bool(all_values[1]):
        raise exception

    for value in all_values:
        if value:
            return value


# handle lhost inputs
def get_ip(ip, interface):
    return get_exclusive({ip: ip, interface: netifaces.ifaddresses(interface)[2][0]["addr"]}, click.BadParameter("Must enter ip or interface"))

def get_shell(template, shell, shell_dir):
    return get_exclusive({template: template.read(), shell: load(shell_dir, shell)}, click.BadParameter("Must enter a shell or shell template")), shell if shell else template.name
        
def make_generated_directory():
    if not os.path.isdir(GENERATED_SHELLS):
        os.mkdir(GENERATED_SHELLS)

def get_extension(extension, language, command_extensions):
    if extension:
        return extension
    elif language in command_extensions:
        return command_extensions[language]
    else:
        return ".txt"


def create_shell(reverse_shell, language, extension):
    make_generated_directory()
    shell_path = os.path.join(GENERATED_SHELLS, f"{language}{extension}")
    try:
        with click.open_file(shell_path, "w") as f:
            f.write(reverse_shell)

    except:
        raise click.UsageError("File not created")

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
    "bash": ".sh", 
    "groovy": ".groovy", 
    "java": ".java",
    "netcat": ".txt",
    "perl": ".pl",
    "php": ".php",
    "python": ".py",
    "ruby": ".rb",
    "telnet": ".txt",
    "xterm": ".txt",
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
@click.option("-l", "--listen", "listen", type=click.Choice([server.SERVER_NAME for server in SUPPORTED_FILE_SERVERS]), prompt=True)
@click.option("-e", "--extension", "extension", type=str)
@click.argument("port", type=int)
def generate(shell, template, ip, interface, listen, extension, port):
    raw_shell, shell_name = get_shell(template, shell, SHELL_PATH)
    lhost = get_ip(ip, interface)
    reverse_shell = inject(raw_shell, lhost, port)
    extension = get_extension(extension, shell, COMMAND_EXTENSIONS)
    create_shell(reverse_shell, shell_name, extension)
    click.echo("Shell Generated Successfully")
    listen_on(listen, port)


if __name__ == "__main__":
    generate()
