# Final user install script to setup a bunch of user-level stuff.
# Must *NOT* be ran as root!

from subprocess import check_output, CalledProcessError
from time import sleep
from sys import exit
from os import system

packages = 'plasma kde-applications firefox lightdm lightdm-gtk-greeter'

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
    log('info', 'Installing xorg packages, and optional packages')
    system(f'sudo pacman -S xorg {packages}')

    log('info', 'Installing and setting up PulseAudio')
    system(f'sudo pacman -S pulseaudio')

    (rc, _) = run('systemctl --user enable pulseaudio.service')
    if rc == 0:
        log('success', 'Successfully enabled the PulseAudio service!')
    else:
        log('error', 'Failed to enable the PulseAudio service!')
        exit(1)
    
install()
