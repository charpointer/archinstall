# This script will be automatically downloaded before entering the chroot.
# Edit as needed, then make sure to run it inside the chroot

from subprocess import check_output, CalledProcessError
from time import sleep
from sys import exit
from os import system

# Variables
keymap = ('uk', 'gb') # vconsole, xserver
timezone = 'Europe/London'
lang = 'en_US'
hostname = 'unicorn'

use_efi = True

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
    log('success', 'We are now chrooted into the new install!')
    
    # The rest of the install continues inside a chroot

    # Set the timezone
    log('info', 'Setting the timezone and running hwclock --systohc')

    run(f'ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime')
    run('hwclock --systohc')

    # Generate locales
    log('info', 'Opening up /etc/locale.gen for editing')
    sleep(2)
    system('vim /etc/locale.gen')

    (rc, _) = run('locale-gen')
    if rc == 0:
        log('success', 'Successfully (re)generated locales!')
    else:
        log('error', 'Failed to generate locales')
        exit(1)

    log('info', 'Generating /etc/locale.conf')
    run(f'echo "LANG={lang}.UTF-8" > /etc/locale.conf')

    # Keyboard layout
    log('info', 'Making keyboard changes persistent in /etc/vconsole.conf')
    run(f'echo "KEYMAP={keymap[0]}" > /etc/vconsole.conf')

    # Setup the hostname
    log('info', 'Creating /etc/hostname')
    run(f'echo "{hostname}" > /etc/hostname')

    log('info', 'Opening up /etc/hosts for editing')
    log('info', 'Please follow https://wiki.archlinux.org/index.php/Hostname')
    sleep(2)
    system('vim /etc/hosts')

    log('info', 'Setting up root password. Please enter a new password for root.')
    system('passwd')

    # # Updating pacman
    # log('info', 'Updating pacman database')
    # system('pacman -Syu')

    # Install GRUB
    log('info', 'Installing GRUB')
    system('pacman -S dosfstools os-prober grub intel-ucode')

    if use_efi:
        efi_par = input('Which partition is your EFI partition? ')
        run('mkdir /boot/efi')
        (rc, _) = run(f'mount {efi_par} /boot/efi')

        if rc == 0:
           log('success', f'Successfully mounted {efi_par} to /boot/efi')
        else:
            log('error', f'Failed to mount {efi_par} to /boot/efi')
            exit(1)

    log('info', 'Running grub-install and grub-mkconfig')

    if use_efi:
        log('info', f'Installing GRUB to EFI ({efi_par}')
        run('grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=grub --recheck')
    else:
        root_par = input('Which partition is your root partition? ')

        log('info', f'Installing GRUB to BIOS/MBR')
        run(f'grub-install {root_par}')
    sleep(1)

    run('grub-mkconfig -o /boot/grub/grub.cfg')

    # Enable dhcpcd service
    system('systemctl enable dhcpcd')

    log('success', 'Successfully(?) installed GRUB. Type "exit" to exit the chroot')

    

install()