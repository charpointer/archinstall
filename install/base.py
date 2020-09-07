from subprocess import check_output, CalledProcessError
from time import sleep
from sys import exit
from os import system

# Variables
keymap = ('uk', 'gb') # vconsole, xserver
timezone = 'Europe/London'
lang = 'en_US'
hostname = 'unicorn'

mountpoint = '/mnt'

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
    log('info', 'Doing some initial stuff, like loading keymaps and connecting to the internet')
    log('info', 'For a base install, no Wifi is supported so this will have to be installed manually')

    log('info', f'Loading keymap ({keymap[0]})')
    run(f'loadkeys {keymap[0]}')

    # Connect to the internet
    log('info', 'Attempting to connect to the internet..')
    run('ip link')
    (rc, _) = run('ping -c 1 archlinux.org')
    if rc == 0:
        log('success', 'The internet seems to be working!')
    else:
        log('error', 'Could not connect to the internet')
        exit(1)

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
    system('pacstrap /mnt base linux linux-firmware dhcpcd vim')

    # Generate an fstab file
    log('info', 'Generating an fstab file')
    run('genfstab -U /mnt >> /mnt/etc/fstab')

    # Download chroot.py
    log('info', 'Downloading chroot install script..')
    url = 'https://raw.githubusercontent.com/chxrlt/archinstall/master/install/chroot.py'
    run(f'curl -L "{url}" > /mnt/chroot.py')

    log('info', 'Entering a chroot, make sure to run chroot.py when inside!')
    system('arch-chroot /mnt')

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

install()