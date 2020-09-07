# This script will be automatically downloaded after post install
# when the bootloader has been setup and installed correctly

from subprocess import check_output, CalledProcessError
from time import sleep
from sys import exit
from os import system

# Utility functions
def log(level, msg):
    color = '\033[34m'
    if level == 'info':
        color = '\033[34m'
    elif level == 'success':
        color = '\033[92m'
    elif level == 'warn':
        color = '\033[93m'
    elif level == 'error':
        color = '\033[91m'

    level = level.upper()
    print(f'[{color}{level}\033[0m] {msg}')

def run(cmd):
    # Wrapper around subprocess.check_output
    try:
        output = check_output(cmd.split(' '))
        return (0, output)
    except CalledProcessError as e:
        return (e.returncode, '')

def install():
    log('success', 'Starting post-install script')
    
    # Install sudo
    log('info', 'Installing sudo')
    system('pacman -S sudo')

    # Create a new user account
    username = input('Enter your username: ')

    log('info', f'Creating a new user account for {username}')
    (rc, _) = run(f'useradd -m -G wheel {username}')

    if rc == 0:
        system(f'passwd {username}')
        log('success', f'Successfully created a new user account for {username}!')
    else:
        log('error', f'Failed to create a new user account for {username}!')
        exit(1)

    # Enable sudo for the user
    system('EDITOR=vim visudo')

    # Download user install script
    log('info', 'Downloading user install script..')
    system(f'curl -L https://raw.githubusercontent.com/chxrlt/archinstall/master/install/userinstall.py > /home/{username}/userinstall.py')

    system('exit && reboot')

install()