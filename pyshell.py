import click
import os
import netifaces


# return all shell commands
def get_all_options(path):
    raw_shells = os.listdir(path=path)
    return [ os.path.splitext(language)[0] for language in raw_shells ]

def load(shell_directory, command):
    try:
        command_path = f"{shell_directory}/{command}.txt"
        with click.open_file(command_path, 'r') as f:
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
        return netifaces.ifaddresses(interface)[2][0]['addr']
    else:
        raise click.BadParameter("Must enter ip or interface")

def get_extension(extension, language, command_extensions):
    if extension:
        return extension
    elif language in command_extensions:
        return command_extensions[language]
    else:
        raise click.BadParameter("Must have valid file extension")

def create_shell(reverse_shell, language, extension):
    shell_path = language + extension
    try:
        with click.open_file(shell_path, 'w') as f:
            f.write(reverse_shell)

    except:
        raise click.UsageError("File not created")

# path to reverse shells
SHELL_PATH = "shells"
SUPPORTED_LANGUAGES = get_all_options(SHELL_PATH)
SYSTEM_INTERFACES = netifaces.interfaces()
# bash.txt  groovy.txt  java.txt  netcat.txt  perl.txt  php.txt  python.txt  ruby.txt  telnet.txt  xterm.txt
COMMAND_EXTENSIONS = {'bash':'.sh', 'groovy':'.groovy', 'java':'.java', 'netcat':'.txt', 'perl':'.pl', 'php':'.php','python':'.py', 'ruby':'.rb', 'telnet':'.txt', 'xterm':'.txt'}

# main command
@click.command()
@click.option('-l', '--language', 'language', required=True, type=click.Choice(SUPPORTED_LANGUAGES), prompt=True)
@click.option('-i', '--ip', 'ip', type=str)
@click.option('-I', '--interface', 'interface', type=click.Choice(SYSTEM_INTERFACES))
@click.option('-e', '--extension', 'extension', type=str)
# add propmpt?
@click.argument('port', type=int)
def generate(language, ip, interface, extension, port):
    raw_shell = load(SHELL_PATH, language)
    lhost = get_ip(ip, interface)
    reverse_shell = inject(raw_shell,lhost, port)
    extension = get_extension(extension, language, COMMAND_EXTENSIONS)
    create_shell(reverse_shell, language, extension)
    click.echo("Shell Generated Successfully")

if __name__ == "__main__":
    generate()




