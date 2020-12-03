#!/usr/bin/env python3
import signal
signal.signal(signal.SIGHUP, lambda s, f: None)
# pylint: disable=wrong-import-position

import time
import os
import sys
import RPi.GPIO as gpio

if len(sys.argv) != 4:
    print(f"Usage: {sys.argv[0]} [gpio_num] [shutdown_time] [shutdown_command]")
    print("---")
    print("[gpio_num]: broadcom-style gpio id (not raspi pin number)")
    print("[shutdown_time]: time in seconds to shutdown after pin no longer pulled low")
    print("[shutdown_command]: command to run - suggest 'shutdown' or 'reboot'")
    sys.exit()

GPIO_NUM = int(sys.argv[1])
SHUTDOWN_TIMER = int(sys.argv[2])
SHUTDOWN_COMMAND = sys.argv[3]

PIN_STATE = ["low","high"]

gpio.setmode(gpio.BCM)
print(f"Monitoring GPIO {GPIO_NUM} high for {SHUTDOWN_TIMER}s -> run '{SHUTDOWN_COMMAND}'")
gpio.setup(GPIO_NUM, gpio.IN, pull_up_down=gpio.PUD_UP)

last_state = None

shutdown = SHUTDOWN_TIMER
while True:
    state = gpio.input(GPIO_NUM)
    if state != last_state:
        print(f"pin {GPIO_NUM} state is now {PIN_STATE[state]}")
    last_state = state
    if state == 0: # pin low
        shutdown = SHUTDOWN_TIMER
    else:
        shutdown -= 1
        if (shutdown % 10) == 0:
            print(f"pin {GPIO_NUM} still high, shutdown in {shutdown}s")
    
    if shutdown < 0:
        os.system(SHUTDOWN_COMMAND)
    
    time.sleep(1)
    
