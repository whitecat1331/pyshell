import click
import os
import netifaces


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


# handle lhost inputs
def get_ip(ip, interface):
    if ip and not interface:
        return ip
    elif not ip and interface:
        return netifaces.ifaddresses(interface)[2][0]["addr"]
    else:
        raise click.BadParameter("Must enter ip or interface")


def get_extension(extension, language, command_extensions):
    if extension:
        return extension
    elif language in command_extensions:
        return command_extensions[language]
    else:
        return ".txt"


def create_shell(reverse_shell, language, extension):
    shell_path = f"{GENERATED_SHELLS}/{language}.{extension}"
    try:
        with click.open_file(shell_path, "w") as f:
            f.write(reverse_shell)

    except:
        raise click.UsageError("File not created")


# path to reverse shells
SHELL_PATH = "template_shells"
SHELL_TEMPLATES = get_all_options(SHELL_PATH)
SYSTEM_INTERFACES = netifaces.interfaces()
GENERATED_SHELLS = "generated_shells"
# bash.txt  groovy.txt  java.txt  netcat.txt  perl.txt  php.txt  python.txt  ruby.txt  telnet.txt  xterm.txt
COMMAND_EXTENSIONS = {
    "bash": ".sh", "groovy": ".groovy", "java": ".java",
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
    required=True,
    type=click.Choice(SHELL_TEMPLATES),
    prompt=True,
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
@click.option("-e", "--extension", "extension", type=str)

@click.argument("port", type=int)
def generate(shell, ip, interface, extension, port):
    raw_shell = load(SHELL_PATH, shell)
    lhost = get_ip(ip, interface)
    reverse_shell = inject(raw_shell, lhost, port)
    extension = get_extension(extension, shell, COMMAND_EXTENSIONS)
    create_shell(reverse_shell, shell, extension)
    click.echo("Shell Generated Successfully")


if __name__ == "__main__":
    generate()
