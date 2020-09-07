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
    run('timedate ctl set-ntp true')

    # Partitioning
    log('info', 'Entering partition()')
    partition()

    # Install base packages with pacstrap
    log('info', 'Opening up /etc/pacman.d/mirrorlist for editing')
    run('vim /etc/pacman.d/mirrorlist')

    log('info', 'Running pacstrap to install base packages')
    run('pacstrap /mnt base linux linux-firmware dhcpcd vim')

    # Generate an fstab file
    log('info', 'Generating an fstab file')
    run('genfstab -U /mnt >> /mnt/etc/fstab')

    chroot_install()

def chroot_install():
    (rc, _) = run('arch-chroot /mnt')
    if rc == 0:
        log('success', 'We are now chrooted into the new install!')
    
    # The rest of the install continues inside a chroot

    # Set the timezone
    log('info', 'Setting the timezone and running hwclock --systohc')

    run(f'ln -sf /usr/share/zoneinfo/{timezone} /etc/localtime')
    run('hwclock --systohc')

    # Generate locales
    log('info', 'Opening up /etc/locale.gen for editing')
    run('vim /etc/locale.gen')

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
    run('vim /etc/hosts')

    log('info', 'Setting up root password. Please enter a new password for root.')
    system('passwd')

    # Install GRUB
    log('info', 'Installing GRUB')
    run('pacman -S dosfstools os-prober grub efibootmgr intel-ucode')

    efi_par = input('Which partition is your EFI partition? ')
    run('mkdir /boot/efi')
    (rc, _) = run(f'mount {efi_par} /boot/efi')

    if rc == 0:
        log('success', f'Successfully mounted {efi_par} to /boot/efi')
    else:
        log('error', f'Failed to mount {efi_par} to /boot/efi')
        exit(1)

    log('info', 'Running grub-install and grub-mkconfig')
    run('grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=grub --recheck')
    sleep(1)
    run('grub-mkconfig -o /boot/grub/grub.cfg')

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