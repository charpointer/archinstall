from subprocess import check_output, CalledProcessError
from time import sleep
from os import system

import argparse
import subprocess
import shutil
import sys

# -----------------------------------------
# Config
# -----------------------------------------

vconsole_keymap = 'uk'
xserver_keymap = 'gb'
ucode = 'intel' # amd for AMD machines

timezone = 'Europe/London'
lang = 'en_US'
hostname = 'arch'

# Set to False to install on BIOS/MBR systems
uefi_install = True

# Extra packages to 'pacstrap' onto the base system
pacstrap_extras = 'vim'

# User packages
user_packages = 'plasma kde-applications firefox'
user_services = 'lightdm.service'

# -----------------------------------------

# Utility functions
def log(level, msg):
    color = '\033[96m'
    if level == 'info':
        color = '\033[96m'
    elif level == 'success':
        color = '\033[92m'
    elif level == 'warn':
        color = '\033[93m'
    elif level == 'error':
        color = '\033[91m'

    level = level.upper()
    print(f'[{color}*{level}*\033[0m] {msg}')

def run(cmd):
    # Wrapper around subprocess.check_output
    try:
        output = check_output(cmd.split(' '))
        return (0, output)
    except CalledProcessError as e:
        return (e.returncode, '')

def install():
    log('info', 'Doing some initial stuff, like loading keymaps and connecting to the internet')
    log('info', 'For a base install, no Wifi is supported so this will have to be installed manually')

    log('info', f'Loading keymap ({vconsole_keymap})')
    run(f'loadkeys {vconsole_keymap}')

    # Connect to the internet
    log('info', 'Attempting to connect to the internet..')
    run('ip link')
    (rc, _) = run('ping -c 1 archlinux.org')
    if rc == 0:
        log('success', 'The internet seems to be working!')
    else:
        log('error', 'Could not connect to the internet')
        sys.exit(1)

    # Update the system clock
    log('info', 'Running timedatectl to update the system clock')
    run('timedatectl set-ntp true')

    # Partitioning
    log('info', 'Entering partition()')
    partition()

    # Install base packages with pacstrap
    log('info', 'Opening up /etc/pacman.d/mirrorlist for editing')
    sleep(2)
    system('vim /etc/pacman.d/mirrorlist')

    log('info', 'Running pacstrap to install base packages')
    system(f'pacstrap /mnt base linux linux-firmware dhcpcd python {pacstrap_extras}')

    # Generate an fstab file
    log('info', 'Generating an fstab file')
    run('genfstab -U /mnt >> /mnt/etc/fstab')

    # Enter a chroot
    log('info', 'Entering a chroot, chrooting in and running installer with --chroot.')
    system('cp install.py /mnt/install.py')
    system('arch-chroot /mnt python3 /mnt/install.py --chroot')

def chroot_install():
    log('success', 'Successfully entered chroot with arch-chroot!')
    
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
        sys.exit(1)

    log('info', 'Generating /etc/locale.conf')
    run(f'echo "LANG={lang}.UTF-8" > /etc/locale.conf')

    # Keyboard layout
    log('info', 'Making keyboard changes persistent in /etc/vconsole.conf')
    run(f'echo "KEYMAP={vconsole_keymap}" > /etc/vconsole.conf')

    # Setup the hostname
    log('info', 'Creating /etc/hostname')
    run(f'echo "{hostname}" > /etc/hostname')

    log('info', 'Opening up /etc/hosts for editing')
    log('info', 'Please follow https://wiki.archlinux.org/index.php/Hostname')
    sleep(2)
    system('vim /etc/hosts')

    log('info', 'Setting up root password. Please enter a new password for root.')
    system('passwd')

    # Install GRUB
    log('info', 'Installing GRUB')
    system(f'pacman -S dosfstools os-prober grub {ucode}-ucode')

    if uefi_install:
        # UEFI installation
        efi_par = input('Which partition is your EFI partition? ')
        run('mkdir /boot/efi')
        (rc, _) = run(f'mount {efi_par} /boot/efi')

        if rc == 0:
           log('success', f'Successfully mounted {efi_par} to /boot/efi')
        else:
            log('error', f'Failed to mount {efi_par} to /boot/efi')
            sys.exit(1)

    log('info', 'Running grub-install and grub-mkconfig')

    if uefi_install:
        # UEFI installation
        log('info', f'Installing GRUB to EFI ({efi_par}')
        run('grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=grub --recheck')
    else:
        root_par = input('Which disk is your root partition? ')

        log('info', f'Installing GRUB to BIOS/MBR')
        run(f'grub-install {root_par}')
    sleep(1)

    run('grub-mkconfig -o /boot/grub/grub.cfg')

    # Enable dhcpcd service
    system('systemctl enable dhcpcd')

    log('success', 'Successfully(?) installed GRUB. Type "exit" to "exit" the chroot')

    # Download the post install script
    log('info', 'Running post install script')
    system('python3 install.py --postinstall')

def post_install():    
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
        sys.exit(1)

    # Enable sudo for the user
    system('EDITOR=vim visudo')

    # Download user install script
    log('info', 'Running userinstall script..')
    system(f'cp install.py /home/{username}/install.py')
    system(f'sudo -u {username} -H /bin/bash -c "python3 /home/{username}/install.py --user"')

def user_install():
    # This "script" will be ran and executed as the new user
    
    log('info', 'Installing xorg packages, and optional packages')
    system(f'sudo pacman -S xorg {user_packages}')

    # Setup PulseAudio
    log('info', 'Installing and setting up PulseAudio')
    system(f'sudo pacman -S pulseaudio')

    (rc, _) = run('systemctl --user enable pulseaudio.service')
    if rc == 0:
        log('success', 'Successfully enabled the PulseAudio service!')
    else:
        log('error', 'Failed to enable the PulseAudio service!')
        sys.exit(1)

    # Enable user services
    services = user_services.split(' ')
    for service in services:
        # Enable the lightdm service
        log('info', f'Enabling {service}.service')

        (rc, _) = run(f'systemctl enable {service}.service')
        if rc == 0:
            log('success', f'Successfully enabled {service}.service!')
        else:
            log('error', f'Failed to enable {service}.service!')
            sys.exit(1)


def partition():
    # Partion wizard to ease and automate partitioning the disks

    run('clear')

    log('info', 'Welcome to charlotte\'s partition wizard!')
    log('info', 'To list all the disks, type "lsdisks". To partition a disk, type "pardisk".')

    exit_wizard = False
    while not exit_wizard:
        prompt = input('? ')

        if prompt == 'lsdisks':
            # Since we don't care about the return code of fdisk -l, use os.system
            # to preserve the formatting.
            system('sudo fdisk -l')
        elif prompt == 'exit':
            log('success', 'Exiting partition()')
            exit_wizard = True
        elif prompt == 'pardisk':
            # Partition the disk
            disk = input('Which disk to partition? ')

            log('info', f'Running cfdisk on {disk}')
            system(f'cfdisk {disk}')
        
            log('info', 'Finished running cfdisk, resuming partition process')

            root_par = input('Which partition is your root partition? ')
            log('info', f'Making root partition ({root_par}) of type ext4 on {disk}')

            run(f'mkfs.ext4 {root_par}')
            log('success', f'Made a root partition ({root_par}) of type ext4 on {disk}')

            # Swap partition is optional
            swap = input('Do you want to make a swap partition? ')
            if swap.lower() == 'y':
                swap_par = input('Which partition is your swap partition? ')
                run(f'mkswap {swap_par}')

                log('success', f'Made a swap partition ({swap_par}) on {disk}')
                run(f'swapon {swap_par}')
            
            log('info', f'Mounting {root_par} to /mnt')
            run(f'mount {root_par} /mnt')

            log('success', 'Finished partitioning! To exit the wizard, type "exit"')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--chroot', action='store_true', help='Run install_chroot to install from within a chroot')
    parser.add_argument('--postinstall', action='store_true', help='Run the post installation script')
    
    args = parser.parse_args()
    
    # Check if we are in the installer environment first
    in_installer = shutil.which('pacstrap') is not None
    if not in_installer:
        log('error', 'Failed to detect an installer environment')
        sys.exit(1)

    if args.chroot:
        log('success', 'pacstrap is present, we seem to be in the installer environment!')

        log('info', 'Proceeding with chroot installation')
        chroot_install()
    elif args.postinstall:
        post_install()
    else:
        install()