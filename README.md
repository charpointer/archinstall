```
      _                _       _   _       
  ___| |__   __ _ _ __| | ___ | |_| |_ ___ 
 / __| '_ \ / _` | '__| |/ _ \| __| __/ _ \
| (__| | | | (_| | |  | | (_) | |_| ||  __/
 \___|_| |_|\__,_|_|  |_|\___/ \__|\__\___|
                                           
 charlotte's semi-automated arch install scripts
```

## Usage
`curl -L https://git.io/JUnze > install.sh && chmod +x install.sh && ./install.sh install` 

Make sure to edit `install.sh` before running, this is a breakdown of the options available for editing.

```
root_disk=""            # used internally by mbr to autodetect the disk

vconsole_keymap="uk"    # keymap for use in vconsole/tty
xorg_keymap="gb"        # keymap for use in xserver, not implemented yet
ucode="intel"           # intel or amd microcode
bios="bios"             # efi or bios

hostname="arch"         # hostname of the system
timezone="Europe/London"# timezone to use in the format of Region/City
lang="en_US"            # language to use

pascstrap_extras="vim"  # any extra packages to bootstrap with pacstrap

# user packages to install
user_packages="firefox lightdm lightdm-gtk-greeter pulseaudio xfce4"

# user services to enable
user_services=(lightdm.service)
```