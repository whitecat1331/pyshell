from setuptools import setup

setup(
    name='pyshell',
    version='1.0.1',
    py_modules=['pyshell'],
    install_requires=[
        'click',
        'netifaces',
        ],
    entry_points={
        'console_scripts': [
            'pyshell = pyshell:generate',
        ],
    },
)
