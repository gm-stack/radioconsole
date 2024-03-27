# Bluetooth TNC to DireWolf - Howto

How to host a bluetooth serial port service on a Raspberry Pi, and connect incoming connections to a TCP socket on localhost.

## Why?

When running Direwolf as a TNC, it can handle beaconing from the GPS by itself, so for that purpose there's no need to connect another APRS client.

However to realise the full benefit of having an AX.25 node, rather than just blindly pushing out position reports, we would like to be able to send and receive messages, as well as be able to look at the locations of other stations. 

To do this of course requires an APRS client to connect to Direwolf, on a device other than the headless Pi.

APRSDroid is such a client for Android, which supports KISS-over-TCP, and this works well - except for one problem. When Android's connected to a WiFi network and that network becomes disconnected from the internet, Android disconnects from the network entirely, rather than just changing the default route to go via the mobile network. This means that you are now no longer receiving messages from the Direwolf server, until you manually reconnect to the network.

So we can connect via Bluetooth, independently of the network, like we would to a handheld radio that includes a TNC (like the LanchonLH HG-UV98).

## Installation

`apt-get install bluez`

## Configuration - BlueZ

Edit `/etc/systemd/system/bluetooth.target.wants/bluetooth.service`

(perhaps we should use an override file instead?)

Modify the commandline arguments to enable the legacy interface and disable the SAP plugin.

The legacy interface is required to be able to use `sdptool` and `rfcomm`. There appears to be no similar tool for the non-legacy interface, although maybe at some point I'll find one (or write one).

(the SAP plugin is "SIM Access Protocol" - used to share the SIM in your mobile phone with a car head unit. For some reason Debian decided to enable this by default. It fails to load every time because no drivers for it even exist that will run on a desktop Linux machine.)

```
ExecStart=/usr/libexec/bluetooth/bluetoothd --compat --noplugin=sap
```

and then run `systemctl daemon-reload`, followed by `service bluetooth restart`.

### Configuration - talking to Direwolf

Create `/etc/systemd/system/rfcomm.service`

```
[Unit]
Description=RFCOMM service
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=simple
ExecStartPre=/usr/bin/sdptool add sp
ExecStart=/usr/bin/rfcomm --raw watch /dev/hci0 1 socat -d -d -v tcp4:127.0.0.1:8001 {}
Restart=always
RestartSec=5s
RemainAfterExit=no
SendSIGHUP=no

[Install]
WantedBy=multi-user.target
```
This runs `rfcomm` as a systemd service.

The `ExecStartPre` block has `sdptool` register a `sp` (serial port) service on the Bluetooth device, at the default channel `1`.

In the `ExecStart` command, `rfcomm` is started in `watch` mode to listen for incoming bluetooth connections on the device `hci0` and channel `1`. When a device connects to the serial port, it opens a new TTY and runs the specified command. 

The specified command is `socat` which connects between `tcp4:127.0.0.1:8001` - the Direwolf server's KISS-over-TCP port and `{}` which is substituted with the TTY that `rfcomm` creates for the connection. 

Run `systemctl daemon-reload`, followed by `service rfcomm start`. Check on it with `service rfcomm status` and `journalctl -fu rfcomm.service`

## Bluetooth setup

Run `hciconfig -a` - if you see that there is no bluetooth device present, double-check things are set up properly.

If on a Raspberry Pi, and you see that the device's Bluetooth address is `00:00:00:00:00:00` or `AA:AA:AA:AA:AA:AA`, check that the `pi-bluetooth` package is installed and if running a 64 bit kernel, you may need `dtoverlay=kernelbt=on` in `/boot/config.txt`. Some revisions of the Pi don't have the address programmed into the Bluetooth controller, instead they generate one on boot from the Pi's serial numebr.

Run `bluetoothctl` and you'll be dropped into a commandline.

Run `show` and check that your bluetooth adaptor shows up.

Then run `discoverable on` and `pairable on`. On your Android device, go to pair a new Bluetooth device, and it should now show up with the device name being the hostname of the Pi. Pair to it, and you'll be prompted in the terminal to confirm passcode and accept the pairing request.

After that's paired, then run `pairable off` and `discoverable off` to take the device out of pairing mode.

You should then be able to launch APRSDroid, select the device as a bluetooth TNC and then press the "Start Tracking" button to connect.

## Still to figure out

- Something in the SDP still isn't correct - Mac OS X doesn't see the serial port in System Profiler, but it does show up in `/dev` on the Mac. I should test it with `QTH.app` and see if it works. I haven't tested this with anything other than APRSDroid on Android, where it does work.