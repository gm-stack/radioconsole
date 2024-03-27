# GPSd Difficulties

There's two issues with the way GPSd is set up out of the box on Raspbian / Debian.

## Problem 1: "Every serial device is a GPS"

Taking a leaf out of NetworkManager's book, where all serial ports could only ever be a dialup modem, `gpsd`'s SystemD config out of the box believes that every USB-Serial device that's plugged into your box must therefore be a GPS.

This caused a whole bunch of bug reports to be filed as it effectively prevented the use of other USB-Serial devices like the Arduino, so the behaviour was changed slightly - excluding `pl2303` and `ftdi` devices. 

This is equally unhelpful because our current USB GPS uses an FTDI chip, and our previous one was `pl2303`. So instead we're just going to tell it which device is our GPS.

### udev rules

We need to write some `udev` rules to find our GPS. Figure out which `/dev/ttyUSB<n>` it is via whatever means (up to and including just unplugging everything else).

Then run `udevadm info -a -n /dev/ttyUSB<n>`. It'll print out a bunch of properties of the device we can match on. One of them that should be present is `serial` - the USB serial number of the device. If your USB-serial converter doesn't have a serial number, you can match on other attributes instead - potentially falling back on USB device path - but you'll have to use the same USB port every time.

Add to a file `/etc/udev/rules.d/70-gps.rules`.

```
ACTION=="add", SUBSYSTEM=="usb", ATTR{serial}=="<serial number from above>", SYMLINK+="gps" RUN+="stty -F /dev/gps 115200" 
```

Edit `/lib/udev/rules.d/60-gpsd.rules` and comment it all out.

Run `udevadm control --reload-rules && udevadm trigger` to reload rules and retrigger on devices. You should now have a `/dev/gps`.

Now edit `/etc/default/gpsd` 

```
# Start the gpsd daemon automatically at boot time
START_DAEMON="true"

# Use USB hotplugging to add new USB devices automatically to the daemon
USBAUTO="false"

# Devices gpsd should collect to at boot time.
# They need to be read/writeable, either by user gpsd or the group dialout.
DEVICES="/dev/gps"

# Other options you want to pass to gpsd
GPSD_OPTIONS="-G -b -n"
```

So of the options: 
- `-G` makes gpsd listen on all interfaces. This won't actually work (yet) - see the next section.
- `-b` makes gpsd not try to write to the device or mess with the baud rate. The GPS I have has been configured carefully in u-blox u-center to use u-blox binary at 115200 baud, 4pps. The higher baud rate means much lower latency, and 4PPS for more frequent updates. GPSD tries to reset it to old-school 4800 baud NMEA every time so it can do autobaud detection - it's unreliable with binary protocol. We know what baud it's at, and `udev` has already set it with `stty`.
- `-n` makes gpsd open the serial port at startup and listen to the GPS all the time - not just when a client's connected. This is more useful for some GPSes that switch off when DTR is not asserted, so they'll drop their fix between clients connecting/disconnecting.


## Problem 2: GPSd won't bind to `0.0.0.0` even with `-G` set!?

So you've added `-G` to `gpsd`'s flags, and it's still binding to localhost?

```
# netstat -lnp | grep 2947
```

SystemD is using some `cgroups` magic to deny it the ability to bind to any interface except localhost. Edit `/lib/systemd/system/gpsd.socket.d/socket.conf` (or was it in `/etc`?) and change it such that ListenStream is `0.0.0.0:2947`. 

```
ListenStream=0.0.0.0:2947
```

`service gpsd restart` (reload config) and it should now be available to other devices on your local network (like, say, your radioconsole pi). 

Be aware that if you do expose this port to the open internet, anyone can connect and see your physical location.