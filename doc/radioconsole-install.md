# Radioconsole Install Notes

Install [Raspberry Pi OS](https://www.raspberrypi.org/downloads/raspberry-pi-os/) onto your card and boot up.

Is your touchscreen upside down? Add `lcd_rotate=2` to `/boot/config.txt` and reboot. There's some dispute between different case manufacturers about which way is up, and the Raspberry Pi foundation changed their mind as well.

Don't use `display_rotate` if you're using the official touchscreen - that will rotate in software which is slower.

## SSH setup

Run `sudo raspi_config` and set the following:
- Menu 1 -> Change your password
- Menu 2 -> Set up your WLAN network
- Menu 3 -> Set boot settings to console-only with no auto-login
- Menu 3 -> Disable wait for network on boot
- Menu 5 -> Enable SSH

Generate a SSH key, making sure it is in PEM format. The current stable version of paramiko does not support the new openssh format keys.

```bash
ssh-keygen -m pem
```

Copy the key generated under the pi user to root.

```bash
sudo cp -R ~/.ssh ~root/
```

Allow the root user to connect back in as pi over SSH (used for raspi_status)

```bash
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
```

## Install libraries

Install some of the required libraries through apt-get to allow downloading binaries rather than building from source, saving a bit of time.

```bash
sudo apt-get install python3-pip python3-numpy python3-pygame cython3 libfftw3-dev librtlsdr-dev python3-scipy python3-paramiko
```

## Install Radioconsole

```bash
sudo apt-get install git
git clone git@github.com:gm-stack/radioconsole.git
cd radioconsole
```

## Install the rest of the dependencies

```bash
sudo pip3 install -r requirements.txt
```

## Install the driver for FT5406 touchscreen controllers

```bash
git clone https://github.com/pimoroni/python-multitouch
cd python-multitouch
sudo ./install
```

## Configure

Edit config.yml (ok, you don't have to use `vim`).

```bash
sudo apt-get install vim
cp config.yaml.example config.yaml
vim config.yaml
```

## Start at boot

Install the SystemD service for radioconsole to make it start on boot:

```bash
sudo cp radioconsole.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable radioconsole
sudo systemctl start radioconsole
```

## Panadapter config

If using the rtlsdr panadapter (if you don't know what that is, you probably won't) - also, this can go on another Pi if the rtlsdr isn't plugged into this one:

```bash
cp waterfall_server.service /etc/systemd/system/
sudo systemctl daemon-reload
systemctl enable waterfall_server
systemctl start waterfall_server
```

## Boot speedups

Add `disable_splash=1`, `dtoverlay=pi3-disable-bt` (if on pi3), `boot_delay=0` to /boot/cmdline.txt to save about 5-7 seconds on boot.
